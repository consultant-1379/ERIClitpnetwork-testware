"""
Data file for network tests
"""
MS_STORAGE_NICS = ['eth1']
MN_STORAGE_NICS = ['eth2', 'eth3']
MS_SERVICES_NICS = ['eth0', 'eth3', 'eth4', 'eth5']
MN_SERVICES_NICS = ['eth0', 'eth1']

#######################################################################
#################### testset_story13259.py ############################
########## test_01_p_create_update_bond_valid_arp_miimon_props ########
#######################################################################

BOND_NAME = "b_13259"
BOND_DEVICE_NAME = 'bond13259'
NETWORK_NAME = "test1"
MODE = "1"
ARP_VALIDATE = "active"
MIIMON = ["100", "0"]
ARP_INTERVAL = ["200", "400"]
ARP_ALL_TARGETS = ["all", "any"]
SUBNET = "70.70.70.0/24"
MS_IP = ["70.70.70.42", "70.70.70.142"]
NODE1_IP = ["70.70.70.43", "70.70.70.143"]
NODE2_IP = ["70.70.70.44", "70.70.70.144"]

ARP_IP_TARGET = [MS_IP[0], NODE2_IP[1], MS_IP[1], NODE2_IP[1]]

IPV6ADDRESSES = ["2001:abcd:ef::42", "2001:abcd:ef::43", "2001:abcd:ef::44"]
UPDATE_IPV6ADDRESSES = ["2001:abcd:ef::142", "2001:abcd:ef::143",
                        "2001:abcd:ef::144"]
ARP_IP_TARGET_FILE = "/sys/class/net/{0}/bonding/arp_ip_target" \
    .format(BOND_DEVICE_NAME)

###########################TEST 1################################
BOND_MS = {"NAME": BOND_NAME,
               "ITEM_PARENT": "ms1_network",
               "TYPE": "bond",
               "PROPS": {'device_name': BOND_DEVICE_NAME,
                         'mode': MODE,
                         'miimon': MIIMON[0],
                         'network_name': NETWORK_NAME,
                         'ipaddress': MS_IP[0],
                         'ipv6address': IPV6ADDRESSES[0]},
               "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                          "IPADDR": MS_IP[0],
                          "mode": MODE,
                          "miimon": MIIMON[0]},
               "NODE": "ms",
               "DELETE_PROPS": False}

MS_ETH = {"NAME": "if_13259",
          "ITEM_PARENT": "ms1_network",
          "TYPE": "eth",
          "PROPS": {"macaddress": "",
                    "device_name": "",
                    "master": BOND_DEVICE_NAME},
          "NODE": ""}

TEST01_NETWORK_MS = {"NAME": "test_network13259",
                     "ITEM_PARENT": "network",
                     "TYPE": "network",
                     "PROPS": {"name": NETWORK_NAME,
                               "subnet": SUBNET},
                     "NODE": "ms"}

CREATE_ITEMS_MS = [TEST01_NETWORK_MS, MS_ETH, BOND_MS]

VCS_NETWORK_HOST = {"NAME": "nh_b_13259_ms",
                      "ITEM_PARENT": "vcs_network_host",
                      "TYPE": "vcs-network-host",
                      "PROPS": {"network_name": NETWORK_NAME,
                                "ip": MS_IP[0]},
                      "NODE": "node2"}

NODE1_ETH = {"NAME": "if_13259",
             "ITEM_PARENT": "node1_network",
             "TYPE": "eth",
             "PROPS": {"macaddress": "",
                       "device_name": "",
                       "master": BOND_DEVICE_NAME},
             "NODE": ""}

NODE1_BOND = {"NAME": BOND_NAME,
              "ITEM_PARENT": "node1_network",
              "TYPE": "bond",
              "PROPS": {"device_name": BOND_DEVICE_NAME,
                        "ipv6address": IPV6ADDRESSES[1],
                        "ipaddress": NODE1_IP[0],
                        "network_name": NETWORK_NAME,
                        "mode": MODE,
                        "arp_interval": ARP_INTERVAL[0],
                        "arp_ip_target": ARP_IP_TARGET[0],
                        "arp_validate": ARP_VALIDATE,
                        "arp_all_targets": ARP_ALL_TARGETS[0]},
              "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                         "IPV6ADDR": IPV6ADDRESSES[1],
                         "IPADDR": NODE1_IP[0],
                         "mode": MODE},
              "NODE": "node1",
              "DELETE_PROPS": False}

NODE1_VCS_NETWORK_HOST = {"NAME": "nh_b_13259_n1",
                          "ITEM_PARENT": "vcs_network_host",
                          "TYPE": "vcs-network-host",
                          "PROPS": {"network_name": NETWORK_NAME,
                                    "ip": NODE1_IP[0]},
                          "NODE": "node1"}

NODE2_ETH = {"NAME": "if_13259",
             "ITEM_PARENT": "node2_network",
             "TYPE": "eth",
             "PROPS": {"macaddress": "",
                       "device_name": "",
                       "master": BOND_DEVICE_NAME},
             "NODE": ""}

NODE2_BOND = {"NAME": BOND_NAME,
              "ITEM_PARENT": "node2_network",
              "TYPE": "bond",
              "PROPS": {"device_name": BOND_DEVICE_NAME,
                        "ipv6address": IPV6ADDRESSES[2],
                        "ipaddress": NODE2_IP[0],
                        "network_name": NETWORK_NAME,
                        "mode": MODE,
                        "arp_interval": ARP_INTERVAL[0],
                        "arp_ip_target": ARP_IP_TARGET[0],
                        "arp_validate": ARP_VALIDATE,
                        "arp_all_targets": ARP_ALL_TARGETS[0]},
              "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                         "IPV6ADDR": IPV6ADDRESSES[2],
                         "IPADDR": NODE2_IP[0],
                         "mode": MODE},
              "NODE": "node2",
              "DELETE_PROPS": False}

NODE2_VCS_NETWORK_HOST = {"NAME": "nh_b_13259_n2",
                          "ITEM_PARENT": "vcs_network_host",
                          "TYPE": "vcs-network-host",
                          "PROPS": {"network_name": NETWORK_NAME,
                                    "ip": NODE2_IP[0]},
                          "NODE": "node2"}


CREATE_ITEMS_NODES = [NODE1_ETH, NODE1_BOND, NODE1_VCS_NETWORK_HOST,
                      NODE2_ETH, NODE2_BOND, NODE2_VCS_NETWORK_HOST,
                      VCS_NETWORK_HOST]

BOND_ITEMS = [BOND_MS, NODE1_BOND, NODE2_BOND]

###########################TEST 2################################

UPDATE_BOND_MS = {"NAME": BOND_NAME,
                      "ITEM_PARENT": "ms1_network",
                      "TYPE": "bond",
                      "PROPS": {"device_name": BOND_DEVICE_NAME,
                                "mode": MODE,
                                "miimon": MIIMON[1],
                                "network_name": NETWORK_NAME,
                                "ipaddress": MS_IP[0],
                                "ipv6address": UPDATE_IPV6ADDRESSES[0]},
                      "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                 "IPADDR": MS_IP[0],
                                 "mode": MODE,
                                 "IPV6ADDR": UPDATE_IPV6ADDRESSES[0],
                                 "miimon": MIIMON[1]},
                      "NODE": "ms",
                      "UPDATE": True}
NEW_VCS_NETWORK_HOST = {"NAME": "nh_b_13259_ms_new",
                          "ITEM_PARENT": "vcs_network_host",
                          "TYPE": "vcs-network-host",
                          "PROPS": {
                              "network_name": NETWORK_NAME,
                              "ip": MS_IP[1]},
                          "NODE": "node1",
                          "UPDATE": False}

UPDATE_NODE1_BOND = {"NAME": BOND_NAME,
                     "ITEM_PARENT": "node1_network",
                     "TYPE": "bond",
                     "PROPS": {
                         "ipaddress": NODE1_IP[1],
                         "ipv6address": UPDATE_IPV6ADDRESSES[1],
                         "arp_ip_target": ARP_IP_TARGET[1],
                         "arp_interval": ARP_INTERVAL[1],
                         "arp_all_targets": ARP_ALL_TARGETS[1]},
                     "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                "IPV6ADDR": UPDATE_IPV6ADDRESSES[1],
                                "IPADDR": NODE1_IP[1],
                                "mode": MODE,
                                "arp_all_targets": ARP_ALL_TARGETS[1]},
                     "NODE": "node1",
                     "UPDATE": True}

NEW_NODE1_VCS_NETWORK_HOST = {"NAME": "nh_b_13259_n1_new",
                              "ITEM_PARENT": "vcs_network_host",
                              "TYPE": "vcs-network-host",
                              "PROPS": {
                                  "network_name": NETWORK_NAME,
                                  "ip": NODE1_IP[1]},
                              "NODE": "node1",
                              "UPDATE": False}

UPDATE_NODE2_BOND = {"NAME": BOND_NAME,
                     "ITEM_PARENT": "node2_network",
                     "TYPE": "bond",
                     "PROPS": {
                         "ipaddress": NODE2_IP[0],
                         "ipv6address": UPDATE_IPV6ADDRESSES[2],
                         "arp_ip_target": ARP_IP_TARGET[0],
                         "arp_interval": ARP_INTERVAL[1],
                         "arp_all_targets": ARP_ALL_TARGETS[1]},
                     "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                "IPV6ADDR": UPDATE_IPV6ADDRESSES[2],
                                "IPADDR": NODE2_IP[0],
                                "mode": MODE,
                                "arp_all_targets": ARP_ALL_TARGETS[1]},
                     "NODE": "node2",
                     "UPDATE": True}

NEW_NODE2_VCS_NETWORK_HOST = {"NAME": "nh_b_13259_n2_new",
                              "ITEM_PARENT": "vcs_network_host",
                              "TYPE": "vcs-network-host",
                              "PROPS": {
                                  "network_name": NETWORK_NAME,
                                  "ip": NODE2_IP[1]},
                              "NODE": "node2",
                              "UPDATE": False}

UPDATE_ITEMS = [UPDATE_BOND_MS,
                UPDATE_NODE1_BOND,
                NEW_NODE1_VCS_NETWORK_HOST,
                UPDATE_NODE2_BOND,
                NEW_NODE2_VCS_NETWORK_HOST,
                NEW_VCS_NETWORK_HOST]

NEW_BOND_ITEMS = [UPDATE_BOND_MS, UPDATE_NODE1_BOND,
                  UPDATE_NODE2_BOND]

###########################TEST 3################################

DELETE_MIIMON_BOND_MS = {"NAME": BOND_NAME,
                         "ITEM_PARENT": "ms1_network",
                         "TYPE": "bond",
                         "PROPS": {"miimon": "miimon"},
                         "CONFIG": {"DEVICE": BOND_DEVICE_NAME},
                         "NODE": "ms",
                         "DELETE_PROPS": True}

DELETE_ARP_PROPS_BOND_NODE1 = {"NAME": BOND_NAME,
                               "ITEM_PARENT": "node1_network",
                               "TYPE": "bond",
                               "PROPS": {"arp_interval": "arp_interval",
                                         "arp_ip_target": "arp_ip_target",
                                         "arp_validate": "arp_validate",
                                         "arp_all_targets": "arp_all_targets"},
                               "CONFIG": {"DEVICE": BOND_DEVICE_NAME},
                               "NODE": "node1",
                               "DELETE_PROPS": True}

DELETE_ARP_PROPS_BOND_NODE2 = {"NAME": BOND_NAME,
                               "ITEM_PARENT": "node2_network",
                               "TYPE": "bond",
                               "PROPS": {"arp_interval": "arp_interval",
                                         "arp_ip_target": "arp_ip_target",
                                         "arp_validate": "arp_validate",
                                         "arp_all_targets": "arp_all_targets"},
                               "CONFIG": {"DEVICE": BOND_DEVICE_NAME},
                               "NODE": "node2",
                               "DELETE_PROPS": True}

DELETE_BOND_PROPS = [DELETE_MIIMON_BOND_MS, DELETE_ARP_PROPS_BOND_NODE1,
                    DELETE_ARP_PROPS_BOND_NODE2]

###########################TEST 4################################

BOND_ARP_MS = {"NAME": BOND_NAME,
                  "ITEM_PARENT": "ms1_network",
                  "TYPE": "bond",
                  "PROPS": {"device_name": BOND_DEVICE_NAME,
                            "mode": MODE,
                            "network_name": NETWORK_NAME,
                            "ipaddress": MS_IP[1],
                            "ipv6address": UPDATE_IPV6ADDRESSES[0],
                            "arp_ip_target": ARP_IP_TARGET[1],
                            "arp_interval": ARP_INTERVAL[1],
                            "arp_all_targets": ARP_ALL_TARGETS[1],
                            "arp_validate": ARP_VALIDATE
                            },
                  "NODE": "ms",
                  "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                             "IPADDR": MS_IP[1],
                             "IPV6ADDR": UPDATE_IPV6ADDRESSES[0],
                             "mode": MODE,
                             "arp_interval": ARP_INTERVAL[1],
                             "arp_ip_target": ARP_IP_TARGET[1],
                             "arp_validate": ARP_VALIDATE},
                  "DELETE_PROPS": False}

NODE1_BOND_MIIMON = {"NAME": BOND_NAME,
                     "ITEM_PARENT": "node1_network",
                     "TYPE": "bond",
                     "PROPS": {"device_name": BOND_DEVICE_NAME,
                               "mode": MODE,
                               "miimon": MIIMON[0],
                               "network_name": NETWORK_NAME},
                     "NODE": "node1",
                     "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                "IPV6ADDR": UPDATE_IPV6ADDRESSES[1],
                                "IPADDR": NODE1_IP[1],
                                "mode": MODE,
                                "miimon": MIIMON[0]},
                     "DELETE_PROPS": False}

NODE2_BOND_MIIMON = {"NAME": BOND_NAME,
                     "ITEM_PARENT": "node2_network",
                     "TYPE": "bond",
                     "PROPS": {"device_name": BOND_DEVICE_NAME,
                               "mode": MODE,
                               "miimon": MIIMON[0],
                               "network_name": NETWORK_NAME},
                     "NODE": "node2",
                     "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                "IPV6ADDR": UPDATE_IPV6ADDRESSES[2],
                                "IPADDR": NODE2_IP[0],
                                "mode": MODE,
                                "miimon": MIIMON[0]},
                     "DELETE_PROPS": False}

UPDATE_ADD_BOND_PROPS = [BOND_ARP_MS, NODE1_BOND_MIIMON,
                           NODE2_BOND_MIIMON]

###########################TEST 5################################

DELETE_ARP_PROPS_BOND_MS = {"NAME": BOND_NAME,
                            "ITEM_PARENT": "ms1_network",
                            "TYPE": "bond",
                            "PROPS": {"arp_interval": "arp_interval",
                                      "arp_ip_target": "arp_ip_target",
                                      "arp_validate": "arp_validate",
                                      "arp_all_targets": "arp_all_targets"},
                            "CONFIG": {"DEVICE": BOND_DEVICE_NAME},
                            "NODE": "ms",
                            "DELETE_PROPS": True}

DELETE_MIIMON_BOND_NODE1 = {"NAME": BOND_NAME,
                            "ITEM_PARENT": "node1_network",
                            "TYPE": "bond",
                            "PROPS": {"miimon": "miimon"},
                            "NODE": "node1",
                            "DELETE_PROPS": True}

DELETE_MIIMON_BOND_NODE2 = {"NAME":  BOND_NAME,
                            "ITEM_PARENT": "node2_network",
                            "TYPE": "bond",
                            "PROPS": {"miimon": "miimon"},
                            "NODE": "node2",
                            "DELETE_PROPS": True}

DELETE_PROP_MIIMON = [DELETE_ARP_PROPS_BOND_MS, DELETE_MIIMON_BOND_NODE1,
                      DELETE_MIIMON_BOND_NODE2]

ADD_MIIMOM_PROPS_MS = {"NAME": BOND_NAME,
                       "NODE": "ms",
                       "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                  "IPADDR": MS_IP[0],
                                  "mode": MODE,
                                  "miimon": MIIMON[0]}}

ADD_ARP_PROPS_NODE1 = {"NAME": BOND_NAME,
                       "NODE": "node1",
                       "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                  "IPADDR": NODE1_IP[0],
                                  "mode": MODE,
                                  "arp_ip_target": ARP_IP_TARGET[0],
                                  "arp_validate": "active",
                                  "arp_interval": "200",
                                  "arp_all_targets": ARP_ALL_TARGETS[0]}}

ADD_ARP_PROPS_NODE2 = {"NAME": BOND_NAME,
                       "NODE": "node2",
                       "CONFIG": {"DEVICE": BOND_DEVICE_NAME,
                                  "IPADDR": NODE2_IP[0],
                                  "mode": MODE,
                                  "arp_ip_target": ARP_IP_TARGET[0],
                                  "arp_validate": "active",
                                  "arp_interval": "200",
                                  "arp_all_targets": ARP_ALL_TARGETS[0]}}

ADD_ARP_PROP = [ADD_MIIMOM_PROPS_MS, ADD_ARP_PROPS_NODE1, ADD_ARP_PROPS_NODE2]

###########################TEST 6################################

UPDATE_MII_PROPS_MS = {"NAME": BOND_NAME,
                       "ITEM_PARENT": "ms1_network",
                       "TYPE": "bond",
                       "PROPS": {
                           "mode": MODE,
                           "miimon": MIIMON[1],
                           "ipaddress": MS_IP[1],
                           "ipv6address": UPDATE_IPV6ADDRESSES[0]},
                       "NODE": "ms",
                       "CONFIG": {
                           "DEVICE": BOND_DEVICE_NAME,
                           "IPADDR": MS_IP[1],
                           "mode": MODE,
                           "miimon": MIIMON[1],
                           "IPV6ADDR": UPDATE_IPV6ADDRESSES[0]},
                       "UPDATE": True}

UPDATE_ARP_PROPS_NODE1 = {"NAME": BOND_NAME,
                          "ITEM_PARENT": "node1_network",
                          "TYPE": "bond",
                          "PROPS": {
                              "arp_interval": ARP_INTERVAL[1],
                              "arp_ip_target": ARP_IP_TARGET[0],
                              "ipaddress": NODE1_IP[1],
                              "ipv6address": IPV6ADDRESSES[1]},
                          "NODE": "node1",
                          "CONFIG": {
                              "DEVICE": BOND_DEVICE_NAME,
                              "IPV6ADDR": IPV6ADDRESSES[1],
                              "IPADDR": NODE1_IP[1],
                              "mode": MODE,
                              "arp_interval": ARP_INTERVAL[1],
                              "arp_ip_target": ARP_IP_TARGET[0]},
                          "UPDATE": True}

UPDATE_ARP_PROPS_NODE2 = {"NAME": BOND_NAME,
                          "ITEM_PARENT": "node2_network",
                          "TYPE": "bond",
                          "PROPS": {
                              "arp_interval": ARP_INTERVAL[1],
                              "arp_ip_target": ARP_IP_TARGET[0],
                              "ipaddress": NODE2_IP[1],
                              "ipv6address": IPV6ADDRESSES[2]},
                          "NODE": "node2",
                          "CONFIG": {
                              "DEVICE": BOND_DEVICE_NAME,
                              "IPV6ADDR": IPV6ADDRESSES[2],
                              "IPADDR": NODE2_IP[1],
                              "mode": MODE,
                              "arp_interval": ARP_INTERVAL[1],
                              "arp_ip_target": ARP_IP_TARGET[0]},
                          "UPDATE": True}

UPDATE_ARP_PROPS = [UPDATE_MII_PROPS_MS, UPDATE_ARP_PROPS_NODE1,
                    UPDATE_ARP_PROPS_NODE2]


#####################
# testset_story2072 #
#####################

# test_04_p_create_vlan2_eth1_same_net_if
TEST04_NET_PROPS = [
    {
        "name": "test1",
        "subnet": "10.10.10.0/24"
    },
    {
        "name": "test2",
        "subnet": "20.20.20.0/24"
    },
    {
        "name": "test3",
        "subnet": "30.30.30.0/24"
    }
]

# test_06_p_create_update_vlan1_eth1_no_ipaddress
TEST06_NET_PROPS = [
    {
        "name": "test1",
        "subnet": None
    },
    {
        "name": "test2",
        "subnet": None
    }
]

########################
# testset_story6629.py #
########################

DEFAULT_BR_OPTIONS = ('BRIDGING_OPTS="multicast_snooping=1 multicast_querier=0'
                      ' multicast_router=1 hash_max=512')

# Test01
TEST01_HOST_PROPS = {
    "6629_01_1": "network_name=test2 ip='fe05::2'",
    "6629_01_2": "network_name=test2 ip='fe05::3'",
    "6629_01_3": "network_name=test2 ip='0.10.10.22'",
    "6629_01_4": "network_name=test2 ip='0.10.10.23'"
}

TEST01_MS_BR_PROPS = [
    'DEVICE="br6629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.21"',
    'IPV6ADDR="fe05::1"',
    DEFAULT_BR_OPTIONS
]

TEST01_N1_BR_PROPS = [
    'DEVICE="br6629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.22"',
    'IPV6ADDR="fe05::2"',
    DEFAULT_BR_OPTIONS
]

TEST01_N2_BR_PROPS = [
    'DEVICE="br6629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.23"',
    'IPV6ADDR="fe05::3"',
    DEFAULT_BR_OPTIONS
]

TEST01_MS_VLAN_PROPS = [
    'BRIDGE="br6629"',
    'VLAN="yes"'
]

TEST01_N1_VLAN_PROPS = [
    'BRIDGE="br6629"',
    'VLAN="yes"'
]

TEST01_N2_VLAN_PROPS = [
    'BRIDGE="br6629"',
    'VLAN="yes"'
]

# Test02
TEST02_MS_BRIDGE = "ipaddress='10.10.10.21' device_name='br6629' " \
                        "ipv6address='fe05::1' network_name='test2'"

TEST02_N1_BRIDGE = "ipaddress='10.10.10.22' device_name='br6629' " \
                        "ipv6address='fe05::2' network_name='test2'"
TEST02_N1_BOND = "device_name='bond629' bridge='br6629' miimon='100' " \
                    "primary_reselect=1 primary={0} mode=1"

TEST02_N2_BRIDGE = "ipaddress={0} device_name='br6629' " \
                    "ipv6address={1} network_name='test2'"
TEST02_N2_BOND = "device_name='bond629' bridge='br6629' miimon='100' " \
                 "primary_reselect=1 primary={0}"

TEST02_HOST_PROPS = {
    "2064_02_1": "network_name=test2 ip='fe05::2'",
    "2064_02_2": "network_name=test2 ip='fe05::3'",
    "2064_02_3": "network_name=test2 ip='10.10.10.22'",
    "2064_02_4": "network_name=test2 ip='10.10.10.23'"
}

TEST02_MS_BR_PROPS = [
    'DEVICE="br6629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.21"',
    'IPV6ADDR="fe05::1"',
    DEFAULT_BR_OPTIONS
]

TEST02_N1_BR_PROPS = [
    'DEVICE="br6629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.22"',
    'IPV6ADDR="fe05::2"',
    DEFAULT_BR_OPTIONS
]

TEST02_N2_BR_PROPS = [
    'DEVICE="br6629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.23"',
    'IPV6ADDR="fe05::3"',
    DEFAULT_BR_OPTIONS
]

TEST02_MS_BOND_PROPS = [
    'DEVICE="bond629"',
    'TYPE="Bonding"',
    'BRIDGE="br6629"',
    'BONDING_OPTS="miimon=100 mode=1"'
    #'miimon="100" mode="1"',
]

# N1 bond props defined in test due to need of dynamic data

TEST02_N2_BOND_PROPS = [
    'DEVICE="bond629"',
    'TYPE="Bonding"',
    'BRIDGE="br6629"',
    'miimon=100 mode=1'
]

TEST02_UPDATED_N1_BOND_PROPS = [
    'DEVICE="bond629"',
    'TYPE="Bonding"',
    'BRIDGE="br6629"',
    'BONDING_OPTS="miimon=100 mode=1"'
]

# Test03
TEST03_MS_BR = "ipaddress='10.10.10.21' device_name='br629' " \
                "ipv6address='fe05::1' network_name='test2'"

TEST03_N1_BR = "ipaddress='10.10.10.22' device_name='br629' " \
                "ipv6address='fe05::2' network_name='test2'"

TEST03_N2_BR = "ipaddress='10.10.10.23' device_name='br629' " \
                "ipv6address='fe05::3' network_name='test2'"

TEST03_BR_PROPS = [
    'DEVICE="br629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.21"',
    'IPV6ADDR="fe05::1"'
]

TEST03_VLAN_PROPS = [
    'BRIDGE="br629"',
    'VLAN="yes"'
]

TEST03_BOND_PROPS = [
    'DEVICE="bond629"'
]

TEST03_ETH_PROPS = [
    'MASTER="bond629"',
    'SLAVE="yes"'
]

TEST03_UPDATED_BR = [
    'DELAY="25"',
    'STP="on"'
]

TEST03_UPDATED_BOND = [
    'BONDING_OPTS="miimon=200 mode=6"'
]

# Test04
TEST04_MS_BR = "ipaddress='10.10.10.21' device_name='br629' " \
                    "ipv6address='fe05::1' network_name='test2'"
TEST04_MS_VLAN = "device_name='{0}.629' network_name='test3' " \
                    "ipaddress='10.10.20.21'"

TEST04_N1_BR = "ipaddress='10.10.10.22' device_name='br629' " \
                    "ipv6address='fe05::2' network_name='test2'"
TEST04_N1_VLAN = "device_name='{0}.629' network_name='test3' " \
                    "ipaddress='10.10.20.22'"

TEST04_N2_BR = "ipaddress='10.10.10.23' device_name='br629' " \
                    "ipv6address='fe05::3' network_name='test2'"
TEST04_N2_VLAN = "device_name='{0}.629' network_name='test3' " \
                    "ipaddress='10.10.20.23'"

TEST04_BR_PROPS = [
    'DEVICE="br629"',
    'TYPE="Bridge"',
    'IPADDR="10.10.10.21"',
    'IPV6ADDR="fe05::1"'
]

TEST04_VLAN_PROPS = [
    'VLAN="yes"',
    'IPADDR="10.10.20.21"'
]

# Test05
TEST05_BR_PROPS = [
    'DEVICE="br629"',
    'TYPE="Bridge"'
]

TEST05_BR_N_PROPS = [
    "IPADDR",
    "NETMASK"
]

# Test06
TEST06_BR_PROPS = [
    'DEVICE="br0"',
    'TYPE="Bridge"'
]

TEST06_ETH_N_PROPS = [
    "IPADDR=",
    "IPV6ADDR=",
    "NETMASK="
]

# Test08
TEST08_ETH_N1 = "device_name='{0}' macaddress='FE:54:00:FF:FF:FF' " \
                    "network_name='test2'"

TEST08_BR_PROPS = [
    'DEVICE="br629"',
    'TYPE="Bridge"'
]

TEST08_BR_N_PROPS = [
    "IPADDR",
    "NETMASK"
]

#######################################################################
#################### testset_story2064.py ############################
#######################################################################

VLAN1_ID = 72
CONST_TEST_1 = "test_1"
CONST_TEST_2 = "test_2"
CONST_TEST1 = "test1"
CONST_TEST2 = "test2"

#Test 01
TEST_01_NET_PROPS = [{
    "name": CONST_TEST_1,
    "subnet": "10.10.10.0/24",
    "litp_management": None
}]

TEST_01_MS_IF = [{
    "ipaddress": "10.10.10.24",
    "bridge": None,
    "ipv6address": "2001:aa::1:4",
    "network_name": CONST_TEST_1
}]

TEST_01_NODE1_IF = [{
    "ipaddress": "10.10.10.25",
    "bridge": None,
    "ipv6address": "2001:aa::1:5",
    "network_name": CONST_TEST_1
}]

#Test 03
TEST_03_NET_PROPS = [{
    "name": CONST_TEST_1,
    "subnet": None,
    "litp_management": None
}]

TEST_03_MS_IF = [{
    "ipaddress": None,
    "bridge": None,
    "ipv6address": "2001:abcd:ef::11/64",
    "network_name": CONST_TEST_1
}]

TEST_03_NODE1_IF = [{
    "ipaddress": None,
    "bridge": None,
    "ipv6address": "2001:abcd:ef::12/64",
    "network_name": CONST_TEST_1
}]

#Test 05
TEST_05_NET_PROPS = [{
    "name": CONST_TEST_1,
    "subnet": "10.10.10.0/24",
    "litp_management": None
}]

TEST_05_MS_IF = [{
    "ipaddress": "10.10.10.54",
    "ipv6address": None,
    "bridge": None,
    "network_name": CONST_TEST_1
}]

TEST_05_NODE1_IF = [{
    "ipaddress": "10.10.10.55",
    "ipv6address": None,
    "bridge": None,
    "network_name": CONST_TEST_1
}]

#Test 09
TEST_09_MS_BRIDGE = [{
    "if_name": "br_2064",
    "ipaddress": "10.10.10.101",
    "ipv6address": "2001:abcd:ef::04",
    "network_name": CONST_TEST1
}]

TEST_09_NODE1_BRIDGE = [{
    "if_name": "br_2064",
    "ipaddress": "10.10.10.102",
    "ipv6address": "2001:abcd:ef::05",
    "network_name": CONST_TEST1
}]

TEST_09_INTERFACE = [{
    "ipaddress": None,
    "ipv6address": None,
    "network_name": None,
    "bridge": "br_2064"
}]

TEST_09_NET_PROPS = [{
    "name": CONST_TEST1,
    "subnet": "10.10.10.0/24",
    "litp_management": None
}]

TEST_09_HOST_PROPS = {
    "2064_09_1": "network_name={0} ip='10.10.10.101'".format(
                                                    CONST_TEST1),
    "2064_09_2": "network_name={0} ip='10.10.10.102'".format(
                                                    CONST_TEST1),
    "2064_09_3": "network_name={0} ip='2001:abcd:ef::04'".format(
                                                    CONST_TEST1),
    "2064_09_4": "network_name={0} ip='2001:abcd:ef::05'".format(
                                                    CONST_TEST1),
    "2064_09_5": "network_name={0} ip='2001:cc::8:7'".format(
                                                    CONST_TEST1),
    "2064_09_6": "network_name={0} ip='2001:cc::8:8'".format(
                                                    CONST_TEST1)
}

#Test 10
TEST_10_NET_PROPS = [{
    "name": CONST_TEST1,
    "subnet": None,
    "litp_management": None
}]

TEST_10_IF = [{
    "ipaddress": None,
    "ipv6address": None,
    "network_name": None,
    "bridge": "br_2064"
}]

TEST_10_MS_BRIDGE = [{
    "if_name": "br_2064",
    "ipaddress": None,
    "ipv6address": "2001:abcd:ef::3",
    "network_name": CONST_TEST1
}]

TEST_10_NODE1_BRIDGE = [{
    "if_name": "br_2064",
    "ipaddress": None,
    "ipv6address": "2001:abcd:ef::4",
    "network_name": CONST_TEST1
}]

#Test 15
TEST_15_MS_VLAN = [{
    "vlan_id": VLAN1_ID,
    "ipaddress": "10.10.10.101",
    "ipv6address": "2001:abcf:ef::12",
    "network_name": CONST_TEST1
}]
TEST_15_MS_INTERFACE = [{
    "ipaddress": "20.20.20.101",
    "ipv6address": "2001:1bcd:ef::03",
    "bridge": None,
    "network_name": CONST_TEST2
}]

TEST_15_NODE1_VLAN = [{
    "vlan_id": VLAN1_ID,
    "ipaddress": "10.10.10.102",
    "ipv6address": "2001:abcf:ef::13",
    "network_name": CONST_TEST1
}]

TEST_15_NODE1_INTERFACE = [{
    "ipaddress": "20.20.20.102",
    "ipv6address": "2001:1bcd:ef::04",
    "bridge": None,
    "network_name": CONST_TEST2
}]

TEST_15_MS_NET_PROPS = [
    {
        "name": CONST_TEST1,
        "subnet": "10.10.10.0/24",
        "litp_management": None
    },
    {
        "name": CONST_TEST2,
        "subnet": "20.20.20.0/24",
        "litp_management": None
    }
]

TEST_15_NET_HOSTS = {
    # NET HOSTS FOR ETHS IPV4
    "2064_15_1": "network_name={0} ip='20.20.20.101'".format(
                                                    CONST_TEST2),
    "2064_15_2": "network_name={0} ip='20.20.20.102'".format(
                                                    CONST_TEST2),

    # NET HOSTS FOR VLANS IPV6
    "2064_15_4": "network_name={0} ip='10.10.10.101'".format(
                                                    CONST_TEST1),
    "2064_15_5": "network_name={0} ip='10.10.10.102'".format(
                                                    CONST_TEST1),

    # NET HOSTS FOR ETHS IPV6
    "2064_15_7": "network_name={0} ip='2001:1bcd:ef::3'".format(
                                                    CONST_TEST2),

    # NET HOSTS FOR VLANS IPV6
    "2064_15_8": "network_name={0} ip='2001:abcf:ef::12'".format(
                                                    CONST_TEST1),
    "2064_15_9": "network_name={0} ip='2001:abcf:ef::13'".format(
                                                    CONST_TEST1),

    # NET HOSTS FOR VLANS IPV6 UPDATES
    "2064_15_11": "network_name={0} ip='2001:a2cd:ef::31'".format(
                                                    CONST_TEST1),
    "2064_15_12": "network_name={0} ip='2001:a2cd:ef::32'".format(
                                                    CONST_TEST1)
}

#Test 16
TEST_16_NET_PROPS = [
    {
        "name": CONST_TEST1,
        "subnet": None,
        "litp_management": None
    },
    {
        "name": CONST_TEST2,
        "subnet": "20.20.20.0/24",
        "litp_management": None
    }
]

TEST_16_MS_VLAN = [{
    "vlan_id": VLAN1_ID,
    "ipaddress": None,
    "network_name": CONST_TEST1,
    "ipv6address": "2001:abcc:ef:abc:abc:abc::12"
}]

TEST_16_MS_IF = [{
    "ipaddress": "20.20.20.101",
    "bridge": None,
    "ipv6address": "2001:abcd:ef::07",
    "network_name": CONST_TEST2
}]

TEST_16_NODE1_VLAN = [{
    "vlan_id": VLAN1_ID,
    "ipaddress": None,
    "network_name": CONST_TEST1,
    "ipv6address": "2001:abcc:00ef:0abc::13"
}]

TEST_16_NODE1_IF = [{
    "ipaddress": "20.20.20.102",
    "bridge": None,
    "ipv6address": "2001:abcd:ef::08",
    "network_name": CONST_TEST2
}]

TEST_16_HOST_PROPS = {
    # NET HOSTS FOR VLANS IPV6
    "2064_16_2": "network_name={0} ip='2001:abcc:00ef:0abc::12'".format(
                                                                CONST_TEST1),
    "2064_16_3": "network_name={0} ip='2001:abcc:00ef:0abc::13'".format(
                                                                CONST_TEST1),

    # NET HOSTS FOR VLANS IPV4
    "2064_16_4": "network_name={0} ip='10.10.10.54'".format(CONST_TEST1),
    "2064_16_5": "network_name={0} ip='10.10.10.55'".format(CONST_TEST1),

    # NET HOSTS FOR ETHS IPV6
    "2064_16_7": "network_name={0} ip='2001:abcd:ef::06'".format(CONST_TEST2),
    "2064_16_8": "network_name={0} ip='2001:abcd:ef::07'".format(CONST_TEST2),
    "2064_16_9": "network_name={0} ip='2001:abcd:ef::08'".format(CONST_TEST2)
}

#Test 17
TEST_17_NET_PROPS = [
    {
        "name": CONST_TEST1,
        "litp_management": None,
        "subnet": "10.10.10.0/24"
    },
    {
        "name": CONST_TEST2,
        "litp_management": None,
        "subnet": "20.20.20.0/24"
    }
]

TEST_17_MS_VLAN = [{
    "vlan_id": VLAN1_ID,
    "ipv6address": None,
    "ipaddress": "10.10.10.101",
    "network_name": CONST_TEST1
}]

TEST_17_MS_IF = [{
    "ipaddress": "20.20.20.101",
    "ipv6address": None,
    "bridge": None,
    "network_name": CONST_TEST2
}]

TEST_17_NODE1_VLAN = [{
    "vlan_id": VLAN1_ID,
    "ipv6address": None,
    "ipaddress": "10.10.10.102",
    "network_name": CONST_TEST1
}]

TEST_17_NODE1_IF = [{
    "ipaddress": "20.20.20.102",
    "ipv6address": None,
    "bridge": None,
    "network_name": CONST_TEST2
}]

TEST_17_HOST_PROPS = {
    # NET HOSTS FOR VLANS IPV4
    "2064_17_1": "network_name={0} ip='10.10.10.100'".format(CONST_TEST1),
    "2064_17_2": "network_name={0} ip='10.10.10.102'".format(CONST_TEST1),
    "2064_17_3": "network_name={0} ip='10.10.10.103'".format(CONST_TEST1),

    # NET HOSTS FOR ETHS IPV4
    "2064_17_4": "network_name={0} ip='20.20.20.100'".format(CONST_TEST2),
    "2064_17_5": "network_name={0} ip='20.20.20.102'".format(CONST_TEST2),
    "2064_17_6": "network_name={0} ip='20.20.20.103'".format(CONST_TEST2),

    # NET HOSTS FOR VLANS IPV6
    "2064_17_7": "network_name={0} ip='2001:cc::8:6'".format(CONST_TEST1),
    "2064_17_9": "network_name={0} ip='2001:cc::8:8'".format(CONST_TEST1),
    "2064_17_10": "network_name={0} ip='2001:abcd:ef::15'".format(CONST_TEST1),
    "2064_17_11": "network_name={0} ip='2001:abcd:ef::17'".format(CONST_TEST1)
}

TEST_24_NET_PROPS = [{
    "name": "test1",
    "subnet": "20.20.20.0/24",
    "litp_management": None},
    {"name": "test2",
     "subnet": "30.30.30.0/24",
     "litp_management": None}]

TEST_24_IF_PROPS = [{
    "ipaddress": "20.20.20.17",
    "bridge": None,
    "ipv6address": "::ffff:a0a:1",
    "network_name": "test1"}]


#######################################################################
#################### testset_story182186.py ###########################
########## test_02_p_check_boundary_values_and_idempotency ########
#######################################################################

BOND_NAME_182186 = 'bond_182186.325'

BND_FIRST_SLV_BUF_VALUES = ('0', '2147483647')
ETH_ONLY_BUFFER_VALUE = '512'
BND_SEC_SLV_BUF_VALUES = ('1', '2147483646')
VLAN_ETH_BUFFER_VALUE = '684'
BR_ETH_BUFFER_VALUES = ('1024', '512')
UPD_BND_FIRST_SLV_BUF_VALUES = ('2147483647', '0')
UPD_ETH_ONLY_BUFFER_VALUES = ('1024', '512')
UPD_BND_SEC_SLAVE_BUF_VALS = '21474'
UPD_VLAN_ETH_BUFFER_VALUE = '400'
DEFAULT_MIN_BUFFER_VALUE = '48'
DEFAULT_MAX_BUFFER_VALUE = '4096'

NETWORK_PROPS_182186 = {'/test_network1821860': {"net_name": 'test182186_1',
                                                 "subnet": '25.25.25.0/24'},
                        '/test_network1821861': {"net_name": 'test182186_2',
                                                 "subnet": '26.26.26.0/24'}}

RING_BUFFER_KEY = 'ETHTOOL_OPTS='
RX_ONLY_PROPS = '"-G {0} rx {1}"'
TX_ONLY_PROPS = '"-G {0} tx {1}"'
RING_VALUES_PROPS = '"-G {0} rx {1}; -G {2} tx {3}"'

INTERFACE0 = {'if_182186_0': {'IPv4': '25.25.25.1',
                              'IPv6': None,
                              'network': 'test182186_1',
                              'bridge': None,
                              'bond': None,
                              'vlan': None}}

INTERFACE1 = {'if_182186_1': {'IPv4': None,
                              'IPv6': None,
                              'network': None,
                              'bridge': None,
                              'bond': 'bond_182186',
                              'vlan': None}}

INTERFACE2 = {'if_182186_2': {'IPv4': '26.26.26.1',
                              'IPv6': '2001:2200:82a1:25::264',
                              'network': 'test182186_2',
                              'bridge': 'br_182186_1',
                              'bond': 'bond_182186',
                              'vlan': 'vlan_182186'}}

INTERFACE3 = {'if_182186_3': {'IPv4': '26.26.26.2',
                              'IPv6': '2001:2200:82a1:25::365',
                              'network': 'test182186_2',
                              'bridge': None,
                              'bond': None,
                              'vlan': 'vlan_182186'}}

INTERFACE4 = {'if_182186_4': {'IPv4': '25.25.25.2',
                              'IPv6': None,
                              'network': 'test182186_1',
                              'bridge': 'br_182186_2',
                              'bond': None,
                              'vlan': None}}


NODE1_INTERFACES = [INTERFACE0, INTERFACE1, INTERFACE2]
NODE2_INTERFACES = [INTERFACE3, INTERFACE4]
