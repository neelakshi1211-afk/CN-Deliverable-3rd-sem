"""Ryu OpenFlow 1.3 learning switch with lab-only REST forwarding/block controls."""
import ipaddress
import json
import logging
from ryu.app.wsgi import ControllerBase, WSGIApplication, route
from ryu.base import app_manager
from ryu.controller import ofp_event
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, set_ev_cls
from ryu.lib.packet import ethernet, ether_types, packet
from ryu.ofproto import ofproto_v1_3
from webob import Response

APP_NAME = 'lab_api'

class LabSwitch(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]
    _CONTEXTS = {'wsgi': WSGIApplication}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.datapaths = {}
        self.mac_to_port = {}
        self.blocked = set()
        wsgi = kwargs['wsgi']
        wsgi.register(LabAPI, {APP_NAME: self})

    def add_flow(self, dp, priority, match, actions=None, cookie=0):
        parser, ofp = dp.ofproto_parser, dp.ofproto
        instructions = [parser.OFPInstructionActions(ofp.OFPIT_APPLY_ACTIONS, actions)] if actions else []
        dp.send_msg(parser.OFPFlowMod(datapath=dp, cookie=cookie, priority=priority,
                                      match=match, instructions=instructions))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features(self, ev):
        dp = ev.msg.datapath
        self.datapaths[dp.id] = dp
        p = dp.ofproto_parser
        self.add_flow(dp, 0, p.OFPMatch(), [p.OFPActionOutput(dp.ofproto.OFPP_CONTROLLER,
                                                               dp.ofproto.OFPCML_NO_BUFFER)])
        for ip in self.blocked:
            self.add_flow(dp, 200, p.OFPMatch(eth_type=0x0800, ipv4_src=ip))
        self.logger.info('Connected switch dpid=%s', dp.id)

    @set_ev_cls(ofp_event.EventOFPStateChange, [MAIN_DISPATCHER])
    def state_up(self, ev):
        self.datapaths[ev.datapath.id] = ev.datapath

    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def packet_in(self, ev):
        msg = ev.msg
        dp, parser, ofp = msg.datapath, msg.datapath.ofproto_parser, msg.datapath.ofproto
        in_port = msg.match['in_port']
        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocol(ethernet.ethernet)
        if eth is None or eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return
        learned = self.mac_to_port.setdefault(dp.id, {})
        learned[eth.src] = in_port
        out_port = learned.get(eth.dst, ofp.OFPP_FLOOD)
        actions = [parser.OFPActionOutput(out_port)]
        if out_port != ofp.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=eth.src, eth_dst=eth.dst)
            self.add_flow(dp, 10, match, actions)
        data = msg.data if msg.buffer_id == ofp.OFP_NO_BUFFER else None
        dp.send_msg(parser.OFPPacketOut(datapath=dp, buffer_id=msg.buffer_id,
                                        in_port=in_port, actions=actions, data=data))

    def update_block(self, ip, should_block):
        ip = str(ipaddress.ip_address(ip))
        if ':' in ip:
            raise ValueError('Only IPv4 is supported')
        if should_block:
            self.blocked.add(ip)
        else:
            self.blocked.discard(ip)
        for dp in self.datapaths.values():
            parser, ofp = dp.ofproto_parser, dp.ofproto
            match = parser.OFPMatch(eth_type=0x0800, ipv4_src=ip)
            if should_block:
                self.add_flow(dp, 200, match)
            else:
                dp.send_msg(parser.OFPFlowMod(datapath=dp, command=ofp.OFPFC_DELETE,
                    out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY, priority=200, match=match))
        return ip

    def custom_rule(self, dpid, src, dst, out_port, delete=False):
        dp = self.datapaths.get(dpid)
        if dp is None:
            raise ValueError('Unknown or disconnected dpid')
        if not 1 <= out_port <= 65535:
            raise ValueError('Port must be in 1..65535')
        parser, ofp = dp.ofproto_parser, dp.ofproto
        match = parser.OFPMatch(eth_type=0x0800, ipv4_src=str(ipaddress.IPv4Address(src)),
                                ipv4_dst=str(ipaddress.IPv4Address(dst)))
        if delete:
            dp.send_msg(parser.OFPFlowMod(datapath=dp, command=ofp.OFPFC_DELETE,
                out_port=ofp.OFPP_ANY, out_group=ofp.OFPG_ANY, priority=100, match=match))
        else:
            self.add_flow(dp, 100, match, [parser.OFPActionOutput(out_port)])

class LabAPI(ControllerBase):
    def __init__(self, req, link, data, **config):
        super().__init__(req, link, data, **config)
        self.app = data[APP_NAME]

    def respond(self, data, status=200):
        return Response(body=json.dumps(data).encode(), content_type='application/json', status=status)

    def parse(self, req):
        try:
            body = json.loads(req.body.decode('utf8'))
            if not isinstance(body, dict):
                raise ValueError('JSON object required')
            return body
        except (ValueError, UnicodeDecodeError) as exc:
            raise ValueError('Invalid JSON: ' + str(exc))

    @route('lab', '/api/status', methods=['GET'])
    def status(self, req, **kwargs):
        return self.respond({'switches': sorted(self.app.datapaths), 'blocked_ipv4': sorted(self.app.blocked)})

    @route('lab', '/api/block', methods=['POST'])
    def block(self, req, **kwargs):
        try:
            ip = self.app.update_block(self.parse(req)['ip'], True)
            return self.respond({'action': 'block', 'ip': ip, 'connected_switches': len(self.app.datapaths)})
        except (ValueError, KeyError) as exc:
            return self.respond({'error': str(exc)}, 400)

    @route('lab', '/api/unblock', methods=['POST'])
    def unblock(self, req, **kwargs):
        try:
            ip = self.app.update_block(self.parse(req)['ip'], False)
            return self.respond({'action': 'unblock', 'ip': ip})
        except (ValueError, KeyError) as exc:
            return self.respond({'error': str(exc)}, 400)

    @route('lab', '/api/rule', methods=['POST', 'DELETE'])
    def rule(self, req, **kwargs):
        try:
            body = self.parse(req)
            dpid = int(body['dpid'])
            port = int(body['out_port'])
            self.app.custom_rule(dpid, body['src_ip'], body['dst_ip'], port,
                                 delete=req.method == 'DELETE')
            return self.respond({'action': 'delete' if req.method == 'DELETE' else 'add',
                                 'dpid': dpid, 'src_ip': body['src_ip'],
                                 'dst_ip': body['dst_ip'], 'out_port': port})
        except (ValueError, KeyError, TypeError) as exc:
            return self.respond({'error': str(exc)}, 400)
