import yaml
import copy


def worker_decorator(work_name=None):
    def logging_decorator(func):
        def wrapped_function(records=None, expect=None, deep=1, varies={}, space=4*' '):
            print(space*deep+"*** Smart worker: {} : {} vs {} Args: {}".format(
                work_name, records, expect, varies))
            res = func(records=records, expect=expect,
                       varies=varies, deep=deep, space=space)
            print(space*deep+"*** End Smart worker: {} Return: {}".format(work_name, res))
            return res
        return wrapped_function
    return logging_decorator


@worker_decorator("str_include_worker")
def str_include_worker(records=None, expect=None, varies={}, deep=1, space=4*' '):
    return True if expect in records else False


@worker_decorator("num_tolerance_worker")
def num_tolerance_worker(records=None, expect=None, varies={'tol': 0.01}, deep=1, space=4*' '):
    tol = varies['tol']
    diff = abs(float(records)-float(expect))/float(expect)
    return True if diff <= tol else False


@worker_decorator("num_tolerance_worker")
def num_equal_biger_worker(records=None, expect=None, varies={}, deep=1, space=4*' '):
    return True if float(records) >= float(expect) else False


@worker_decorator("num_tolerance_worker")
def num_equal_smaller_worker(records=None, expect=None, varies={}, deep=1, space=4*' '):
    return True if float(records) <= float(expect) else False


@worker_decorator("art_worker")
def art_worker(records=None, expect=None, varies={}, deep=1, space=4*' '):
    # art: N/A
    # art: 'vm6: N/A'
    if 'N/A' in expect:
        return True if records == expect else False
    if 'diff' in varies.keys():
        diff = varies['diff']
    else:
        diff = 0
    # expected value
    vm_1 = expect.split(': ')[0]
    tmp = expect.split(': ')[1].split('/')
    cnd_1 = float(tmp[0])
    snd_1 = float(tmp[1])

    # real value
    vm = records.split(': ')[0]
    tmp = records.split(': ')[1].split('/')
    cnd = float(tmp[0])
    snd = float(tmp[1])
    if vm == vm_1 and abs(cnd-cnd_1)/cnd_1 <= diff and abs(snd-snd_1)/snd_1 < diff:
        return True
    else:
        return False


def base_engine(expect, records, tol=None, deep=1, space=4*' ', smart_engine={}):

    if type(expect) not in [dict, list] or (type(expect) == list and len(expect) == 0):
        print(space*deep+"{} vs {}".format(expect, records))

    if type(expect) in [int, float]:
        if tol != None and float(expect) != 0:
            diff = abs(expect - int(records))/expect
            print(space*deep+"tol:{} diff:{}".format(tol, diff))
            return diff <= tol
        else:
            return expect == records

    elif type(expect) is bool:
        return records == expect
    # elif type(expect) is unicode:
    #     return expect == records
    elif type(expect) is str:
        return expect == str(records)

    elif type(expect) is list and len(expect) == 0:
        return True if records == [] else False

    elif type(expect) is list and type(expect[0]) is not dict:
        for i in range(len(expect)):
            res = base_engine(expect[i], records[i], tol=tol,
                              deep=2*deep, smart_engine=smart_engine)
            if res == False:
                print(space*deep+"Can't Find Record")
                return False
        return True

    elif type(expect) is list and type(expect[0]) is dict:
        for a_expect in expect:
            print(space*deep+"Try find in list ......")

            find_record = False
            for a_record in records:
                flow_matched = True

                for key in a_expect.keys():
                    if key in smart_engine.keys():
                        worker = smart_engine[key]['worker']
                        varies = smart_engine[key]['var']
                        res = globals()[worker](
                            a_expect[key], a_record[key], 2*deep, varies)
                    else:
                        res = base_engine(
                            a_expect[key], a_record[key], tol=tol, deep=2*deep, smart_engine=smart_engine)

                    if res == False:
                        flow_matched = False
                        break

                if flow_matched == True:
                    print(space*deep+"Entry found in list ......")
                    # Remove the matched a_expect in list
                    records.remove(a_record)
                    find_record = True
                    break

            if find_record == False:
                print(space*deep+"Can't Find Record")
                return False

    elif type(expect) is dict:
        if 'records' in expect.keys():
            if 'record_num' in expect.keys() and expect['record_num'] != None:
                if len(records) != expect['record_num']:
                    print(space*deep+"Entry number do not match!")
                    return False
            for entry in expect['records']:
                find_record = False
                for a_record in records:
                    flow_matched = True
                    for key in entry.keys():
                        if key in smart_engine.keys():
                            worker = smart_engine[key]['worker']
                            varies = smart_engine[key]['var']
                            res = globals()[worker](
                                expect[key], records[key], 2*deep, varies)
                        else:
                            res = base_engine(
                                expect[key], records[key], tol=tol, deep=2*deep, smart_engine=smart_engine)
                        if res == False:
                            flow_matched = False
                            break
                    if flow_matched == True:
                        find_record = True
                        break
                if find_record == False:
                    print(space*deep+"Can't Find Record")
                    return False
        else:
            for key in expect.keys():
                if key in smart_engine.keys():
                    worker = smart_engine[key]['worker']
                    varies = smart_engine[key]['var']
                    res = globals()[worker](
                        expect[key], records[key], 2*deep, varies)
                else:
                    res = base_engine(
                        expect[key], records[key], tol=tol, deep=2*deep, smart_engine=smart_engine)

                if res == False:
                    print(space*deep+"Can't Find Record")
                    return False
    else:
        print("Unknow Condition,Code Extension Work Needed,reach out sish@cisco.com")
        import pdb
        pdb.set_trace()
    return True


def engine_entrance(expect_template={}, rest_data={}):
    if 'smart_engine' in expect_template.keys():
        smart_engine = expect_template['smart_engine']
        expect_template_copy = copy.deepcopy(expect_template)
        expect_template_copy.pop('smart_engine')
    else:
        smart_engine = {}
    return base_engine(expect_template_copy, rest_data, smart_engine=smart_engine)


if __name__ == '__main__':

    dst_48_1_0_5 = {'type': 'hops-of-flow', 'entry_time': 1648012830183, 'trace-id': 528, 'data': {'app_group': 'other', 'app_name': 'http', 'art': 'vm5: 49/51', 'asymmetry_detected': False, 'device_trace_id': 528, 'domain': [], 'domain_name': 'Unknown', 'domain_src': 'no data', 'dpi_policy_used': False, 'dst_ip': '48.1.0.5', 'dst_port': 80, 'flow_id': 9, 'flow_key': '9,16.1.0.39:47699->48.1.0.5:80,TCP', 'flow_moved': False, 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'protocol': 'TCP', 'received_timestamp': 1648012842164, 'start_timestamp': 1648012842164, 'sla_violated': False, 'sla_violated_bfd': False, 'src_ip': '16.1.0.39', 'src_port': 47699, 'start_device': '172.16.255.15', 'tcp_flow_reset': False, 'timestamp': 1648012830183, 'upstream_dscp': 'DEFAULT', 'wan_color_asym': True, 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False, 'downstream_device_list': [{'device_name': 'vm6', 'device_system_ip': '172.16.255.16', 'ingress_pre_invalid': True, 'remoteColor': 'INVALID', 'localColor': 'LTE', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'GOLD', 'remoteSystemIp': '172.16.255.11'}, 'packet_list': [21444]}, {'device_name': 'vm1', 'device_system_ip': '172.16.255.11', 'remoteColor': 'GOLD', 'localColor': 'COLOR_3G', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.16'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback2', 'localColor': 'COLOR_3G', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.15'}, 'packet_list': [11888]}, {'device_name': 'vm5', 'device_system_ip': '172.16.255.15', 'egress_next_invalid': True, 'remoteColor': 'LTE', 'localColor': 'INVALID', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'GigabitEthernet1', 'localColor': 'LTE', 'remoteColor': 'COLOR_3G', 'remoteSystemIp': '172.16.255.11'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'packet_list': [26186]}, {'device_name': 'N/A', 'device_system_ip': 'N/A', 'remoteColor': 'N/A', 'localColor': 'N/A', 'up_fwd_decision': 'unknown', 'down_fwd_decision': 'unknown', 'up_actual_path': {}, 'down_actual_path': {}, 'packet_list': []}], 'upstream_device_list': [{'device_name': 'vm5', 'device_system_ip': '172.16.255.15', 'ingress_pre_invalid': True, 'remoteColor': 'INVALID', 'localColor': 'LTE', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'GigabitEthernet1', 'localColor': 'LTE', 'remoteColor': 'COLOR_3G', 'remoteSystemIp': '172.16.255.11'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'packet_list': [26185]}, {'device_name': 'vm1', 'device_system_ip': '172.16.255.11', 'remoteColor': 'COLOR_3G', 'localColor': 'LTE', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.16'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback2', 'localColor': 'COLOR_3G', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.15'}, 'packet_list': [11887]}, {'device_name': 'vm6', 'device_system_ip': '172.16.255.16', 'egress_next_invalid': True, 'remoteColor': 'LTE', 'localColor': 'INVALID', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'GOLD', 'remoteSystemIp': '172.16.255.11'}, 'packet_list': [21443]}, {'device_name': 'N/A', 'device_system_ip': 'N/A', 'remoteColor': 'N/A', 'localColor': 'N/A', 'up_fwd_decision': 'unknown', 'down_fwd_decision': 'unknown', 'up_actual_path': {}, 'down_actual_path': {}, 'packet_list': []}], 'downstream_dscp': 'DEFAULT', 'downstream_hop_list': [{'art': 'N/A', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 0, 'jitter': '2147483647', 'latency': '1024', 'local_color': 'LTE', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        'local_edge': '(Gi5) vm6', 'local_system_ip': '172.16.255.16', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'GOLD', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm1', 'remote_system_ip': '172.16.255.11', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '437', 'total_packets': '5', 'wan_color_asym': True, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'N/A', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 1, 'jitter': '2147483647', 'latency': '1024', 'local_color': 'COLOR_3G', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm1', 'local_system_ip': '172.16.255.11', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'LTE', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm5', 'remote_system_ip': '172.16.255.15', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '657', 'total_packets': '5', 'wan_color_asym': False, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'N/A', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 2, 'jitter': '2147483647', 'latency': '2147483647', 'local_color': 'Service LAN', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm5 (Gi5)', 'local_system_ip': '172.16.255.15', 'nat_translated': False, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'N/A', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'LAN Side', 'remote_system_ip': '0.0.0.0', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '657', 'total_packets': '5', 'wan_color_asym': False, 'wan_drop_rate': '2147483647.00', 'wan_drop_str': 'N/A', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}], 'upstream_hop_list': [{'art': 'vm5: 49/51', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 0, 'jitter': '0', 'latency': '1024', 'local_color': 'LTE', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': '(Gi5) vm5', 'local_system_ip': '172.16.255.15', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'COLOR_3G', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm1', 'remote_system_ip': '172.16.255.11', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '403', 'total_packets': '5', 'wan_color_asym': True, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'vm1: 50/48', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 1, 'jitter': '2147483647', 'latency': '1024', 'local_color': 'LTE', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm1', 'local_system_ip': '172.16.255.11', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'LTE', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm6', 'remote_system_ip': '172.16.255.16', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '623', 'total_packets': '5', 'wan_color_asym': True, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'vm6: 51/47', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 2, 'jitter': '2147483647', 'latency': '2147483647', 'local_color': 'Service LAN', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm6 (Gi5)', 'local_system_ip': '172.16.255.16', 'nat_translated': False, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'N/A', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'LAN Side', 'remote_system_ip': '0.0.0.0', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '623', 'total_packets': '5', 'wan_color_asym': False, 'wan_drop_rate': '2147483647.00', 'wan_drop_str': 'N/A', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}], 'flow_readout': {'application': 'http', 'totalFlowNumCounted': True, 'totalFlowNumLast15MinsCounted': True, 'flowStartTime': '1648012846643', 'flowLastUpdateTime': '1648012846643', 'domain': [], 'upstream': [], 'downstream': []}}, 'tenant': 'default'}
    dst_48_1_0_5_copy = {'type': 'hops-of-flow', 'entry_time': 1648012830183, 'trace-id': 528, 'data': {'app_group': 'other', 'app_name': 'http', 'art': 'vm5: 49/51', 'asymmetry_detected': False, 'device_trace_id': 528, 'domain': [], 'domain_name': 'Unknown', 'domain_src': 'no data', 'dpi_policy_used': False, 'dst_ip': '48.1.0.5', 'dst_port': 80, 'flow_id': 9, 'flow_key': '9,16.1.0.39:47699->48.1.0.5:80,TCP', 'flow_moved': False, 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'protocol': 'TCP', 'received_timestamp': 1648012842164, 'start_timestamp': 1648012842164, 'sla_violated': False, 'sla_violated_bfd': False, 'src_ip': '16.1.0.39', 'src_port': 47699, 'start_device': '172.16.255.15', 'tcp_flow_reset': False, 'timestamp': 1648012830183, 'upstream_dscp': 'DEFAULT', 'wan_color_asym': True, 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False, 'downstream_device_list': [{'device_name': 'vm6', 'device_system_ip': '172.16.255.16', 'ingress_pre_invalid': True, 'remoteColor': 'INVALID', 'localColor': 'LTE', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'GOLD', 'remoteSystemIp': '172.16.255.11'}, 'packet_list': [21444]}, {'device_name': 'vm1', 'device_system_ip': '172.16.255.11', 'remoteColor': 'GOLD', 'localColor': 'COLOR_3G', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.16'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback2', 'localColor': 'COLOR_3G', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.15'}, 'packet_list': [11888]}, {'device_name': 'vm5', 'device_system_ip': '172.16.255.15', 'egress_next_invalid': True, 'remoteColor': 'LTE', 'localColor': 'INVALID', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'GigabitEthernet1', 'localColor': 'LTE', 'remoteColor': 'COLOR_3G', 'remoteSystemIp': '172.16.255.11'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'packet_list': [26186]}, {'device_name': 'N/A', 'device_system_ip': 'N/A', 'remoteColor': 'N/A', 'localColor': 'N/A', 'up_fwd_decision': 'unknown', 'down_fwd_decision': 'unknown', 'up_actual_path': {}, 'down_actual_path': {}, 'packet_list': []}], 'upstream_device_list': [{'device_name': 'vm5', 'device_system_ip': '172.16.255.15', 'ingress_pre_invalid': True, 'remoteColor': 'INVALID', 'localColor': 'LTE', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'GigabitEthernet1', 'localColor': 'LTE', 'remoteColor': 'COLOR_3G', 'remoteSystemIp': '172.16.255.11'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'packet_list': [26185]}, {'device_name': 'vm1', 'device_system_ip': '172.16.255.11', 'remoteColor': 'COLOR_3G', 'localColor': 'LTE', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.16'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback2', 'localColor': 'COLOR_3G', 'remoteColor': 'LTE', 'remoteSystemIp': '172.16.255.15'}, 'packet_list': [11887]}, {'device_name': 'vm6', 'device_system_ip': '172.16.255.16', 'egress_next_invalid': True, 'remoteColor': 'LTE', 'localColor': 'INVALID', 'up_fwd_decision': 'routing', 'down_fwd_decision': 'routing', 'up_actual_path': {'nextHopType': 'NEXTHOP_SERVICE_LAN', 'outputInterface': 'GigabitEthernet5'}, 'down_actual_path': {'nextHopType': 'NEXTHOP_SDWAN_SESSION', 'outputInterface': 'Loopback1', 'localColor': 'LTE', 'remoteColor': 'GOLD', 'remoteSystemIp': '172.16.255.11'}, 'packet_list': [21443]}, {'device_name': 'N/A', 'device_system_ip': 'N/A', 'remoteColor': 'N/A', 'localColor': 'N/A', 'up_fwd_decision': 'unknown', 'down_fwd_decision': 'unknown', 'up_actual_path': {}, 'down_actual_path': {}, 'packet_list': []}], 'downstream_dscp': 'DEFAULT', 'downstream_hop_list': [{'art': 'N/A', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 0, 'jitter': '2147483647', 'latency': '1024', 'local_color': 'LTE', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00',
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        'local_edge': '(Gi5) vm6', 'local_system_ip': '172.16.255.16', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'GOLD', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm1', 'remote_system_ip': '172.16.255.11', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '437', 'total_packets': '5', 'wan_color_asym': True, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'N/A', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 1, 'jitter': '2147483647', 'latency': '1024', 'local_color': 'COLOR_3G', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm1', 'local_system_ip': '172.16.255.11', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'LTE', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm5', 'remote_system_ip': '172.16.255.15', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '657', 'total_packets': '5', 'wan_color_asym': False, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'N/A', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 2, 'jitter': '2147483647', 'latency': '2147483647', 'local_color': 'Service LAN', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm5 (Gi5)', 'local_system_ip': '172.16.255.15', 'nat_translated': False, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'N/A', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'LAN Side', 'remote_system_ip': '0.0.0.0', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '657', 'total_packets': '5', 'wan_color_asym': False, 'wan_drop_rate': '2147483647.00', 'wan_drop_str': 'N/A', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}], 'upstream_hop_list': [{'art': 'vm5: 49/51', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 0, 'jitter': '0', 'latency': '1024', 'local_color': 'LTE', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': '(Gi5) vm5', 'local_system_ip': '172.16.255.15', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'COLOR_3G', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm1', 'remote_system_ip': '172.16.255.11', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '403', 'total_packets': '5', 'wan_color_asym': True, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'vm1: 50/48', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 1, 'jitter': '2147483647', 'latency': '1024', 'local_color': 'LTE', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm1', 'local_system_ip': '172.16.255.11', 'nat_translated': True, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'LTE', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'vm6', 'remote_system_ip': '172.16.255.16', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '623', 'total_packets': '5', 'wan_color_asym': True, 'wan_drop_rate': '0.00', 'wan_drop_str': '0.00', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}, {'art': 'vm6: 51/47', 'asymmetry_detected': False, 'dpi_policy_used': False, 'fif_dpi_not_classified': False, 'flow_id': 9, 'hop_index': 2, 'jitter': '2147483647', 'latency': '2147483647', 'local_color': 'Service LAN', 'local_drop_cause_num': 0, 'local_drop_rate': '0.00', 'local_edge': 'vm6 (Gi5)', 'local_system_ip': '172.16.255.16', 'nat_translated': False, 'path_changed': False, 'policy_bypassed': False, 'q_d_avg_pkts': 0, 'q_d_max_pkts': 0, 'q_d_min_pkts': 0, 'q_id': 0, 'q_lim_pkts': 0, 'qos_congested': False, 'remote_color': 'N/A', 'remote_drop_cause_num': 0, 'remote_drop_rate': '0.00', 'remote_edge': 'LAN Side', 'remote_system_ip': '0.0.0.0', 'sla_violated': False, 'tcp_flow_reset': False, 'total_bytes': '623', 'total_packets': '5', 'wan_color_asym': False, 'wan_drop_rate': '2147483647.00', 'wan_drop_str': 'N/A', 'appqoe_diverted': False, 'utd_diverted': False, 'big_drop': False}], 'flow_readout': {'application': 'http', 'totalFlowNumCounted': True, 'totalFlowNumLast15MinsCounted': True, 'flowStartTime': '1648012846643', 'flowLastUpdateTime': '1648012846643', 'domain': [], 'upstream': [], 'downstream': []}}, 'tenant': 'default'}
                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                        
    # Usage Example
    sish='/home/cisco/vtest/tests/sessions/trex_cfg_files/nwpi/nwpi_traffic_profile/'
    yamlPath = '48_1_0_5.yaml'
    with open(sish+yamlPath, 'r') as f:
        config = f.read()
    expect_dict = yaml.load(config, Loader=yaml.FullLoader)


    res = engine_entrance(expect_dict, dst_48_1_0_5)
    print(">>>>>>>>")
    res = engine_entrance(expect_dict, dst_48_1_0_5_copy)
    print(res)

    # with open('data.yml', 'w') as outfile:
    #     yaml.dump(dst_48_1_0_4, outfile, default_flow_style=False)
