"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     June 2014
@author:    Kieran Duggan; Alan Conroy
@summary:   Integration
            Agile: STORY-2064
"""

from litp_generic_test import GenericTest, attr
import netaddr
from xml_utils import XMLUtils
import test_constants
import network_test_data as data


class Story2064(GenericTest):
    """
    As a LITP User, I want to create IPs for IPv6 addresses,
    so I can to assign IPv6 address to network interfaces
    """
    test_ms_if1 = None
    test_ms_if2 = None
    test_node_if1 = None
    test_node_if2 = None
    VLAN1_ID = data.VLAN1_ID

    def setUp(self):
        """
        Runs before every single test
        """
        super(Story2064, self).setUp()

        # Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.all_nodes = [self.ms_node] + [self.peer_nodes[0]]

        self.ms_url = "/ms"
        self.node_urls = self.find(self.ms_node, "/deployments", "node")
        self.all_node_urls = [self.ms_url] + [self.node_urls[0]]

        self.ms_net_url = self.find(self.ms_node, self.ms_url,
                                    "collection-of-network-interface")[0]

        self.n1_net_url = self.find(self.ms_node, self.node_urls[0],
                                    "collection-of-network-interface")[0]

        self.xml = XMLUtils()
        self.vcs_cluster_url = self.find(self.ms_node, "/deployments",
                                         "vcs-cluster")[-1]
        self.networks_path = self.find(self.ms_node, "/infrastructure",
                                       "network", False)[0]

    def tearDown(self):
        """
        Run after each test and performs the following:
        """
        super(Story2064, self).tearDown()
        self.check_configured_nodes()

    def _is_ip_in_etc_hosts(self, ipaddress):
        """
        Description:
            Returns True if the ip has been found in an etc hosts file,
            False otherwise
        Args:
            ipaddress (str): The ipaddress to check /etc/hosts for
        Returns:
            (bool) True if ipaddress is in /etc/hosts, false otherwise
        """
        for node in self.all_nodes:
            self.log("info", "NODE={0}".format(node))
            file_contents = self.get_file_contents(
                node, test_constants.ETC_HOSTS, su_root=True)
            if self.is_text_in_list(ipaddress, file_contents):
                return True

        return False

    def check_configured_nodes(self):
        """
        Description:
            Calls deconfig method for nodes that have had interfaces/vlans
            set up on them.
        """
        ms_if_list = [
            self.test_ms_if1,
            self.test_ms_if2
        ]
        node_if_list = [
            self.test_node_if1,
            self.test_node_if2
        ]

        for interface in ms_if_list:
            if interface is not None:
                self.deconfig_interface_and_vlan(self.ms_node,
                                                 interface["NAME"])

        for interface in node_if_list:
            if interface is not None:
                for node in self.peer_nodes:
                    self.deconfig_interface_and_vlan(node, interface["NAME"])

    def deconfig_interface_and_vlan(self, node, if_name):
        """
        Description:
            Deconfigures interface and vlan set up in test for the specified
            node.
        Args:
            node (str): The node the interface/vlan was set up on
            if_name (str): Name of the interface device to be deconfigured
        """
        # DECONFIGURE test interface ON MS
        cmd = "{0} {1}".format(test_constants.IFDOWN_PATH, if_name)
        self.run_command(node, cmd, su_root=True)
        cmd += ".{0}".format(self.VLAN1_ID)
        self.run_command(node, cmd, su_root=True)

        # REMOVE VLAN IFCFG FILE ON MS
        ifcfg_file = "{0}/ifcfg-{1}.{2}".format(
            test_constants.NETWORK_SCRIPTS_DIR, if_name, self.VLAN1_ID)
        self.remove_item(node, ifcfg_file, su_root=True)

    def create_network(self, network_props, first_item=2064):
        """
        Description
            Create networks based on input data
        Args:
            network_props (list): List of network input property dictionaries
        KwArgs:
            first_item (int): Used to create unique network paths. Default
                is 2064
        """
        for index, network_prop in enumerate(network_props, first_item):
            network_url = "{0}/network_{1}".format(self.networks_path, index)
            props = "name='{0}'".format(network_prop["name"])
            if network_prop["subnet"] is not None:
                props += " subnet='{0}'".format(network_prop["subnet"])
            if network_prop["litp_management"] is not None:
                props += " litp_management='{0}'".\
                    format(network_prop["litp_management"])
            self.execute_cli_create_cmd(self.ms_node, network_url,
                                        "network", props)

    def create_vlan(self, vlan_props, node_url, first_item=2064):
        """
        Description
             Create vlans based on input data
        Args:
            vlan_props (list): Vlan input properties
            node_url (str): Url of the node to create the vlan on
        KwArgs:
            first_item (int): Used to create unique network paths. Default
                is 2064
        """
        for index, vlan_prop in enumerate(vlan_props, first_item):
            vlan_node = self.get_node_filename_from_url(self.ms_node, node_url)
            vlan_name = "{0}.{1}".format(vlan_prop["if_name"],
                                         vlan_prop["vlan_id"])
            self.add_nic_to_cleanup(vlan_node, vlan_name)

            net_if = self.find(self.ms_node, node_url,
                               "collection-of-network-interface")[0]
            vlan_url = "{0}/vlan_{1}".format(net_if, index)
            props = "device_name='{0}' network_name='{1}'".\
                format(vlan_name, vlan_prop["network_name"])

            if vlan_prop["ipaddress"] is not None:
                ipaddress = netaddr.IPAddress(vlan_prop["ipaddress"])
                props += " ipaddress='{0}'".format(ipaddress)
            if vlan_prop["ipv6address"] is not None:
                ipv6address = netaddr.IPAddress(vlan_prop["ipv6address"])
                props += " ipv6address='{0}'".format(ipv6address)
            self.execute_cli_create_cmd(self.ms_node, vlan_url,
                                        "vlan", props)

    def create_bridge(self, bridge_props, node_url, first_item=2064):
        """
        Description
            Create bridges based on input data
        Args:
            bridge_props (list): Bridge input properties
            node_url (str): Url of the node to create the bridge on
        KwArgs:
            first_item (int): Used to create unique network interfaces paths.
                Default is 2064
        """
        for index, bridge_prop in enumerate(bridge_props, first_item):
            # cleanup ifcfg file
            br_node = self.get_node_filename_from_url(self.ms_node, node_url)
            self.add_nic_to_cleanup(br_node, bridge_prop["if_name"],
                                    is_bridge=True)
            # CREATE TEST BRIDGE
            net_if = self.find(self.ms_node, node_url,
                               "collection-of-network-interface")[0]
            bridge_url = "{0}/br_{1}".format(net_if, index)
            props = "device_name='{0}' network_name='{1}'".\
                format(bridge_prop["if_name"], bridge_prop["network_name"])
            if bridge_prop["ipaddress"] is not None:
                ipaddress = netaddr.IPAddress(bridge_prop["ipaddress"])
                props += " ipaddress='{0}'".format(ipaddress)
            if bridge_prop["ipv6address"] is not None:
                ipv6address = netaddr.IPAddress(bridge_prop["ipv6address"])
                props += " ipv6address='{0}'".format(ipv6address)
            self.execute_cli_create_cmd(self.ms_node, bridge_url,
                                        "bridge", props)

    def create_interface(self, interface_props, node_url, first_item=2064):
        """
        Description
             Create interfaces based on input data
        Args:
            interface_props (list): interface input properties
            node_url (str): Url of the node to create the interfaces on
        KwArgs:
            first_item (int): Used to create unique interface paths. Default
                is 2064
        """
        for index, interface_prop in enumerate(interface_props, first_item):
            all_nics = self.get_all_nics_from_node(self.ms_node, node_url)

            # GET CORRECT MAC ADDRESS
            macaddress = None
            for nic in all_nics:
                if nic["NAME"] == interface_prop["if_name"]:
                    macaddress = nic["MAC"]
                    break

            # CREATE TEST INTERFACE
            net_if = self.find(self.ms_node, node_url,
                               "collection-of-network-interface")[0]
            if_url = "{0}/if_{1}".format(net_if, index)
            props = "device_name='{0}' macaddress='{1}' ".\
                                format(interface_prop["if_name"], macaddress,
                                            interface_prop["network_name"])
            if interface_prop["network_name"] is not None:
                props += " network_name='{0}'".\
                    format(interface_prop["network_name"])
            if interface_prop["bridge"] is not None:
                props += " bridge='{0}'".format(interface_prop["bridge"])
            if interface_prop.get("ipaddress") is not None:
                ipaddress = netaddr.IPAddress(interface_prop["ipaddress"])
                props += " ipaddress='{0}'".format(ipaddress)
            if interface_prop.get("ipv6address") is not None:
                ipv6address = interface_prop["ipv6address"]
                # Increment addr to avoid address duplication
                # Checking to see if ipv6address contains a subnet prefix
                if "/" not in ipv6address:
                    addr = netaddr.IPAddress(interface_prop["ipv6address"])
                    props += " ipv6address='{0}'".format(addr)
                else:
                    ipaddr, prefix = ipv6address.split("/")
                    addr = netaddr.IPAddress(ipaddr)
                    ip_prop = "{0}/{1}".format(addr, prefix)
                    props += " ipv6address='{0}'".format(ip_prop)
            self.execute_cli_create_cmd(self.ms_node, if_url, "eth", props)

    def xml_verify(self, node_url):
        """
        Description:
            Checks that the xml file created is valid
        Args:
            node_url (str): Url of the node to create the vlan on
        """
        # XML TEST ARTIFACT
        file_path = "xml_expected_story2064.xml"

        # EXPORT CREATED PROFILE ITEM
        network_url = self.find(self.ms_node, node_url,
                                "collection-of-network-interface")[0]
        self.execute_cli_export_cmd(self.ms_node, network_url, file_path)

        # run xml file and assert that it passes
        cmd = self.xml.get_validate_xml_file_cmd(file_path)
        stdout = self.run_command(self.ms_node, cmd, default_asserts=True)[0]
        self.assertNotEqual([], stdout)

    def data_driven_create(self, network_props, vlan_props, bridge_props,
                                interface_props, node_url):
        """
        Description:
            Create test network with given props and create a LITP plan
        Args:
            network_props (list): Network input properties
            vlan_props (list): Vlan input properties
            bridge_props (list): Bridge input properties
            interface_props (list): Interface input properties
            node_url (str): URL of node to configure network on
        """
        self.create_network(network_props)
        self.create_vlan(vlan_props, node_url)
        self.create_bridge(bridge_props, node_url)
        self.create_interface(interface_props, node_url)

    def setup_interface_verify(self, interface_prop, ipaddress, addr,
                               ifcfg_file, errors):
        """
        Description:
            Verifies that the specified interface, bridge or vlan has been
            configured.
            Checks that the relevant ifcfg file has the correct information.
        Args:
            interface_prop (list): A list of dictionaries containing the
                properties the created interfaces/bridges should have
            ipaddress (IPAddress): Ipaddress the interface should have. None
                if not configured
            addr (IPAddress): Ip6adress the interface should have. None if not
                configured
            ifcfg_file (list): Interface file contents
        Returns:
            errors (list): Errors encountered
            ipaddress(str): IPv4 address
            addr(str): IPv6 address
        """
        if interface_prop.get('vlan_id') is not None:
            if not self.is_text_in_list(
                'DEVICE="{0}.{1}"'.format(interface_prop["if_name"],
                                        interface_prop["vlan_id"]),
                    ifcfg_file):
                errors.append('DEVICE="{0}.{1}" is not configured'.
                              format(interface_prop["if_name"],
                                     interface_prop["vlan_id"]))
            if not self.is_text_in_list('VLAN="yes"', ifcfg_file):
                errors.append('VLAN="yes" is not configured')

        if not self.is_text_in_list(
                'DEVICE="{0}'.format(interface_prop["if_name"]),
                ifcfg_file):
            errors.append('DEVICE="{0}" is not configured'.
                          format(interface_prop["if_name"]))

        if interface_prop["ipaddress"] is not None:
            if not self.is_text_in_list(
                    'IPADDR="{0}"'.format(ipaddress),
                    ifcfg_file):
                errors.append('IPADDR="{0}" is not configured'.
                              format(ipaddress))
        if interface_prop["ipv6address"] is not None:
            if not self.is_text_in_list(
                    'IPV6ADDR="{0}'.format(addr),
                    ifcfg_file):
                errors.append('IPV6ADDR="{0}" is not configured'.
                              format(addr))
        if not self.is_text_in_list('BOOTPROTO="static"', ifcfg_file):
            errors.append('BOOTPROTO="static" is not configured')

        if interface_prop.get("bridge") is not None:
            if not self.is_text_in_list('TYPE="Bridge"', ifcfg_file):
                errors.append('TYPE="Bridge" is not configured')

        return errors, ipaddress, addr

    def data_driven_interface_verify(self, interface_props, node_url):
        """
        Description:
            Checks values in the model matches the actual values on the node
        Args:
            interface_props (list): List of dicts of props of interface
                item in model
            node_url (list): URL of node to check interface properties
        Results:
            (list) stderr of checking configuration
        """
        errors = []

        ipaddress = addr = None
        for interface_prop in interface_props:
            if interface_prop["ipaddress"] is not None:
                ipaddress = netaddr.IPAddress(interface_prop["ipaddress"])
            if interface_prop["ipv6address"] is not None:
                ipv6address = interface_prop["ipv6address"]
            # Checking to see if ipv6address contains a subnet prefix
                if "/" in ipv6address:
                    ipaddr, _ = ipv6address.split("/")
                    addr = netaddr.IPAddress(ipaddr)
                else:
                    addr = netaddr.IPAddress(interface_prop["ipv6address"])

            self.log("info", "VERIFYING NODE {0}".format(node_url))
            node_fname = self.get_node_filename_from_url(self.ms_node,
                                                         node_url)

            # CHECK Interface CONFIG FILE EXISTS
            if_name = interface_prop["if_name"]
            if interface_prop.get('vlan_id') is not None:
                if_name += "." + str(interface_prop["vlan_id"])

            path = "{0}/ifcfg-{1}".\
                format(test_constants.NETWORK_SCRIPTS_DIR,
                       if_name)
            dir_contents = self.list_dir_contents(node_fname, path)
            if not dir_contents:
                errors.append("ifcfg-{0} doesn't exist on node {1}".
                              format(if_name), node_url)
            # CHECK Interface FILE CONTENT
            std_out = self.get_file_contents(node_fname, path)

            errors, ipaddress, addr = self.setup_interface_verify(
                interface_prop, ipaddress, addr, std_out, errors)

        return errors

    def chk_multicast_snoop_on_node(self, node_url, bridge_file,
                                    snoop_val="1"):
        """
        Description:
            Checks given bridge ifcfg file has expected multicast_snooping
            value.
        Args:
            node_url (str): url of a node on which to check.
            bridge_file (str): suffix file name of the ifcfg file.
        KwArgs:
            snoop_val (str): value to be searched for. Default is "1"
        """
        br_options = ' multicast_querier=0 multicast_router=1 hash_max=512'
        node_hostname = self.get_node_filename_from_url(self.ms_node, node_url)
        filepath = "{0}/ifcfg-{1}".format(test_constants.NETWORK_SCRIPTS_DIR,
                                          bridge_file)
        stdout = self.get_file_contents(node_hostname, filepath,
                                        assert_not_empty=True)
        option_str = 'BRIDGING_OPTS="multicast_snooping={0}{1}'.\
            format(snoop_val, br_options)
        self.assertTrue(self.is_text_in_list(option_str, stdout))

    def create_vcs_net_host(self, url_id, host_props):
        """
        Description:
            Creates vcs-network-host item under deployment path with given
            props.
        Args:
            url_id (str): URL ID of host item to create
            host_props (str): Properties to be used in the creation.
        """
        net_host_collection = self.find(self.ms_node, self.vcs_cluster_url,
                                        "collection-of-vcs-network-host")[0]
        net_host_url = net_host_collection + "/" + url_id
        self.execute_cli_create_cmd(self.ms_node, net_host_url,
                                    "vcs-network-host", host_props)

    def _ping_sequential_ip6(self, initial_ipaddress, vlan=False):
        """
        Description:
            Loops over ms node and peer nodes and makes sure the supplied
            ipaddresses are pingable.
        Args:
            initial_ipaddress (str): The initial ipaddress to start from.
                The first node will use this address, the next node will use
                the next ip.
                E.g If 2001:abcd:ef::04 is passed in MS will use
                2001:abcd:ef::04, N1 will use 2001:abcd:ef::05, N2 will use
                2001:abcd:ef::06 etc.
        KwArgs:
            vlan (bool): Specifies whether or not to ping vlan.
                 Defaults to false
        """
        ipaddress = netaddr.IPAddress(initial_ipaddress)
        for node in self.all_nodes:
            if node == self.ms_node:
                if_name = self.test_ms_if1["NAME"]
            else:
                if_name = self.test_node_if1["NAME"]

            if vlan:
                cmd = self.net.get_ping6_cmd(ipaddress, 10,
                                             "-I {0}.{1}".format(
                                                 if_name, self.VLAN1_ID))
            else:
                cmd = self.net.get_ping6_cmd(ipaddress, 10, "-I {0}".format(
                    if_name))
            self.run_command(node, cmd, default_asserts=True)
            ipaddress += 1

    def _verify_xml_and_ifcfg(self, verify_props):
        """
        Description:
            Verifies ifcfg file is correct and xml files are valid
        Args:
            verify_props (dict): A dictionary containing dictionaries of props
                to be checked with the node they must be checked on as their
                key
        """
        for node_url, verify in verify_props.iteritems():
            std_err = self.data_driven_interface_verify(verify, node_url)
            self.assertEqual([], std_err)
            self.xml_verify(node_url)

    def update_validate_ipv6address_prop(self, url, props, valid=False):
        """
        Description:
            Updates the ipv6address property and validates it by checking for
            the correct error message.
        Args:
            url(str): Url of the path to update the property on
            props(str): ipv6address property values
            valid(boolean): Specifies whether or not to assert the error
                            message to be "is not valid" or "is not permitted".
                            Default value is False
        """
        std_err = self.execute_cli_update_cmd(
            self.ms_node, url, props, expect_positive=False)[1]

        self.assertTrue(self.is_text_in_list("ValidationError", std_err))
        if valid:
            self.assertTrue(self.is_text_in_list("is not valid", std_err))
        else:
            self.assertTrue(self.is_text_in_list("is not permitted", std_err))

    def create_iface_and_validate(self, url, props, net_type):
        """
        Description:
            Creates an interface with the specified network item and
            validates it by checking for the correct error message.
        Args:
            url(str): Url of the path to update the property on
            props(str): network item properties such as device_name,
                        network_name, ipaddress, ipv6address
            net_type(str): Type of network item.

        """
        stderr = self.execute_cli_create_cmd(
            self.ms_node, url, net_type, props, expect_positive=False)[1]

        self.assertTrue(self.is_text_in_list("ValidationError", stderr))
        self.assertTrue(self.is_text_in_list("is not valid", stderr))

    @attr('all', 'revert', 'story2064', 'story2064_tc01')
    def test_01_p_create_update_valid_interface_non_mgmt_network(self):
        """
        @tms_id: litpcds_2064_tc01
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create update valid interface non mgmt network
        @tms_description: Verify nodes remain pingable after updating ip
            addresses and a validation error is thrown when ipaddress property
            is provided an invalid value. This test now covers
            litpcds_2064_tc08 and litpcds_2064_tc28
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: Item created
        @step: Create eth item on ms and node1
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute /sbin/ip -6 addr show on eth item
        @result: Tentative and dadfailed is not in output
        @step: Ping ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat /etc/sysconfig/network-scripts/ifcfg" on ms and
              node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @step: Update ms and node1 network items ipv6 address
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat /etc/sysconfig/network-scripts/ifcfg" on ms,node1
            and node2 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @step: Update ms and node1 network items ipv6 address to an invalid
            value
        @result: ValidationError thrown with message 'is not valid'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log("info", "1. Create network and interface")
        self.test_node_if1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(
            self.ms_node, self.ms_url)[0]

        if_verify = {}
        vlan_props = []
        bridge_props = []

        # Load network and interface configs
        if_verify[self.ms_url] = data.TEST_01_MS_IF
        if_verify[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]

        if_verify[self.node_urls[0]] = data.TEST_01_NODE1_IF
        if_verify[self.node_urls[0]][0]["if_name"] = self.test_node_if1["NAME"]

        for node, interface in if_verify.iteritems():
            if node == self.ms_url:
                network_props = data.TEST_01_NET_PROPS
            else:
                network_props = []
            self.data_driven_create(
                network_props, vlan_props, bridge_props, interface, node)

        self.log("info", "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "3. Run ip -6 addr show cmd")
        cmd = "{0} -6 addr show {1}".format(
            test_constants.IP_PATH, self.test_ms_if1["NAME"])
        stdout = self.run_command(self.ms_node, cmd)[0]

        self.log("info", "4. Check for invalid flags")
        self.assertFalse(self.is_text_in_list("tentative", stdout))
        self.assertFalse(self.is_text_in_list("dadfailed", stdout))

        self.log("info", "5. Check if interfaces are pingable")
        self._ping_sequential_ip6("2001:aa::1:4")

        self.log("info", "6. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(if_verify)

        self.log("info", "7. Update props")

        ipv6address = netaddr.IPAddress("2001:abcd:ef::2")
        index = 2064
        for node_url in self.all_node_urls:
            net_if = self.find(
                self.ms_node, node_url, "collection-of-network-interface")[0]
            if_url = "{0}/if_{1}".format(net_if, index)
            if_props = "ipv6address='{0}'".format(ipv6address)
            self.execute_cli_update_cmd(self.ms_node, if_url, if_props)
            ipv6address += 1

        self.log("info", "8. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "9. Check if interfaces are pingable")
        self._ping_sequential_ip6("2001:abcd:ef::2")

        if_verify[self.ms_url][0]['ipv6address'] = "2001:abcd:ef::2"
        if_verify[self.node_urls[0]][0]['ipv6address'] = "2001:abcd:ef::3"

        self.log("info", "10. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(if_verify)

        self.log('info', "11. Update MS and Node1's ipv6address property "
                         "to an invalid value this should raise a "
                         "ValidationError")
        props = "ipv6address='test_addr'"
        for url in self.ms_net_url, self.n1_net_url:
            if_url = "{0}/if_2064".format(url)
            self.update_validate_ipv6address_prop(if_url, props, valid=True)

    @attr('all', 'revert', 'story2064', 'story2064_tc02')
    def test_02_n_create_interface_invalid_ipv6_addr(self):
        """
        @tms_id: litpcds_2064_tc02
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create an interface with an invalid ipv6address
        @tms_description: Verify a validation error is thrown when an invalid
            value is given to ipv6 property and valid value is given to ipv4
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: item created
        @step: Create eth item on MS with invalid ipv6address value and valid
            ipv4 value
        @result: ValidationError thrown with message 'is not valid'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        free_nics = self.verify_backup_free_nics(self.ms_node, self.ms_url,
                                                 backup_files=False)[0]
        self.log('info', '1. Create network')
        network_url = "{0}/test_network2064".format(self.networks_path)
        props = "name='test' subnet='20.20.20.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        if_url = "{0}/if2064".format(self.ms_net_url)
        props = "macaddress='{0}' device_name='{1}' network_name='test' " \
                "ipv6address='invalid' ipaddress='20.20.20.22'". \
            format(free_nics["MAC"], free_nics["NAME"])

        self.log('info', '2. Create eth item on MS with invalid ipv6address '
                         'value.')
        self.create_iface_and_validate(if_url, props, 'eth')

    @attr('all', 'revert', 'story2064', 'story2064_tc03', 'cdb_priority1')
    def test_03_p_create_update_convert_interface_ipv6_only(self):
        """
        @tms_id: litpcds_2064_tc03
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create update convert interface ipv6 only
        @tms_description: Verify updating and creating ipv6 property results
            in nodes being pingable, a successful plan and information
            contained in ifcfg is correct
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: Item created
        @step: Create eth item on ms, node1 and node2 with ipv6 property
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat /etc/sysconfig/network-scripts/ifcfg" on ms and
              node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result:  Ms and node1 information is correct
        @step: Update ipv6 address property on ms and node1
        @result: Ms and node1 are ipv6 address property updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat /etc/sysconfig/network-scripts/ifcfg" on ms and
             node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result:  Ms and node1 information is correct
        @step: Update subnet property on network item under 'infrastructure'
        @result: Item updated
        @step: Delete ipv6address property of network_interfaces item
            on ms and node1
        @result: Item updated
        @step: Update ipaddress property of network_interfaces item
            on ms and node1
        @result: Item updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat /etc/sysconfig/network-scripts/ifcfg" on ms and
              node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.test_node_if1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(
            self.ms_node, self.ms_url)[0]

        if_verify = {}
        vlan_props = []
        bridge_props = []

        # Load network and interface configs
        if_verify[self.ms_url] = data.TEST_03_MS_IF
        if_verify[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]

        if_verify[self.node_urls[0]] = data.TEST_03_NODE1_IF
        if_verify[self.node_urls[0]][0]["if_name"] = self.test_node_if1["NAME"]

        self.log("info", "1. Create interfaces for test")
        for node, interface in if_verify.iteritems():
            if node == self.ms_url:
                network_props = data.TEST_03_NET_PROPS
            else:
                network_props = []
            self.data_driven_create(network_props, vlan_props,
                                    bridge_props, interface, node)

        self.log("info", "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "3. Check if interface is pingable")
        self._ping_sequential_ip6("2001:abcd:ef::11")

        self.log("info", "4. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(if_verify)

        self.log("info", "5. Update properties")
        ipv6address = netaddr.IPAddress("2001:abcd:ef::21")
        index = 2064
        for node_url in self.all_node_urls:
            net_if = self.find(
                self.ms_node, node_url, "collection-of-network-interface")[0]
            if_url = "{0}/if_{1}".format(net_if, index)
            if_props = "ipv6address='{0}'".format(ipv6address)
            self.execute_cli_update_cmd(self.ms_node, if_url, if_props)
            ipv6address += 1

        self.log("info", "6. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "7. Check if interface is pingable")
        self._ping_sequential_ip6("2001:abcd:ef::21")

        if_verify[self.ms_url][0]['ipv6address'] = "2001:abcd:ef::21"
        if_verify[self.node_urls[0]][0]['ipv6address'] = "2001:abcd:ef::22"

        self.log("info", "8. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(if_verify)

        self.log("info", "9. Convert network to IPv4")
        net_url = "{0}/network_{1}".format(self.networks_path, index)
        net_props = "subnet='10.10.10.0/24'"
        self.execute_cli_update_cmd(self.ms_node, net_url, net_props)
        ipaddress = netaddr.IPAddress("10.10.10.54")

        self.log("info", "10. Convert interfaces to IPv4")
        for node_url in self.all_node_urls:
            net_if = self.find(
                self.ms_node, node_url, "collection-of-network-interface")[0]
            if_url = "{0}/if_{1}".format(net_if, index)
            self.execute_cli_update_cmd(self.ms_node, if_url,
                                        "ipv6address", action_del=True)
            if_props = "ipaddress='{0}'".format(ipaddress)
            self.execute_cli_update_cmd(self.ms_node, if_url, if_props)
            ipaddress += 1

        self.log("info", "11. Run and check plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "12. Check if interface is pingable")
        ipaddress = netaddr.IPAddress("10.10.10.54")
        for node in self.all_nodes:
            cmd = self.net.get_ping_cmd(str(ipaddress), 10)
            self.run_command(node, cmd, default_asserts=True)
            ipaddress += 1

        if_verify[self.ms_url][0]['ipaddress'] = "10.10.10.54"
        if_verify[self.ms_url][0]['ipv6address'] = None
        if_verify[self.node_urls[0]][0]['ipaddress'] = "10.10.10.55"
        if_verify[self.node_urls[0]][0]['ipv6address'] = None

        self.log("info", "13. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(if_verify)

    # attr('pre-reg', 'revert', '2064')
    def obsolete_04_p_ipv6_to_ipv4_conversion(self):
        """
            This test has been merged with TC03
            Description:
                1.Test creates an interface with and IPv6 address only
                2. update the interface to use ipv4 address
                3. Check that ifcfg files are updated  correctly
                4. Checks that the address can be pinged/ ssh into.
        """
        pass

    @attr('all', 'revert', 'story2064', 'story2064_tc05')
    def test_05_p_ipv4_to_ipv6_conversion(self):
        """
        @tms_id: litpcds_2064_tc05
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Update ipv4 to ipv6
        @tms_description: Verify updating interface items ipv4 address
            to ipv6 results in a successful plan
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: Item created
        @step: Create eth item on ms and node1 with ip4 property
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat ifcfg" on ms and node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @step: Delete subnet property under infrastructure
        @result: Property deleted
        @step: Delete ipaddress property and create ipv6 prop on node1 and ms
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping6 ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat ifcfg" on ms and node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @tms_test_precondition: NA
        @tms_execution_type: Automated

        """
        self.test_node_if1 = self.verify_backup_free_nics(self.ms_node,
                                                          self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.ms_url)[0]

        self.log("info", "1. Create network and interface")
        if_verify = {}
        vlan_props = []
        bridge_props = []

        if_verify[self.ms_url] = data.TEST_05_MS_IF
        if_verify[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]

        if_verify[self.node_urls[0]] = data.TEST_05_NODE1_IF
        if_verify[self.node_urls[0]][0]["if_name"] = self.test_node_if1["NAME"]

        for node, interface in if_verify.iteritems():
            if node == self.ms_url:
                network_props = data.TEST_05_NET_PROPS
            else:
                network_props = []
            self.data_driven_create(network_props, vlan_props,
                                    bridge_props, interface, node)

        self.log("info", "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "3. Check if interfaces are pingable")
        ipaddress = netaddr.IPAddress("10.10.10.54")
        for node in self.all_nodes:
            cmd = self.net.get_ping_cmd(ipaddress, 10)
            self.run_command(node, cmd, default_asserts=True)
            ipaddress += 1

        if_verify[self.ms_url][0]['ipaddress'] = "10.10.10.54"
        if_verify[self.node_urls[0]][0]['ipaddress'] = "10.10.10.55"

        self.log("info", "4. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(if_verify)

        self.log("info", "5. Check that the ip is not in /etc/hosts")
        # New ip is not management network so should not be here.(Story835)
        self.assertFalse(self._is_ip_in_etc_hosts(
            if_verify[self.ms_url][0]['ipaddress']))

        index = 2064
        self.log("info", "6. Update props")
        net_url = "{0}/network_{1}".format(self.networks_path, index)
        self.execute_cli_update_cmd(self.ms_node, net_url,
                                    "subnet", action_del=True)
        ipv6address = netaddr.IPAddress("2001:abcd:ef::11")
        for node_url in self.all_node_urls:
            net_if = self.find(self.ms_node, node_url,
                               "collection-of-network-interface")[0]
            if_url = "{0}/if_{1}".format(net_if, index)
            self.execute_cli_update_cmd(self.ms_node, if_url,
                                        "ipaddress", action_del=True)
            if_props = "ipv6address='{0}'".format(ipv6address)
            self.execute_cli_update_cmd(self.ms_node, if_url, if_props)
            ipv6address += 1

        self.log("info", "7. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "8. Check if interfaces are pingable")
        self._ping_sequential_ip6("2001:abcd:ef::11")

        if_verify[self.ms_url][0]['ipaddress'] = None
        if_verify[self.ms_url][0]['ipv6address'] = "2001:abcd:ef::11"
        if_verify[self.node_urls[0]][0]['ipaddress'] = None
        if_verify[self.node_urls[0]][0]['ipv6address'] = "2001:abcd:ef::12"

        self.log("info", "9. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(if_verify)

    # attr('pre-reg', 'revert', '2064')
    def obsolete_06_p_update_interface_ipv6_addr(self):
        """
            This test has been merged with TC_01
            Description
                1. creates and interface with valid ipv4 and
                    ipv6 addresses.
                2. updates the ipv6 value of the interface
                3. Checks that the IPv6 address can be pinged/ ssh into.
                4. Check that ifcfg files are updated correctly
        """
        pass

    # attr('pre-reg', 'revert', '2064')
    def obsolete_07_p_update_interface_ipv6_addr_only(self):
        """
            This test has been merged with TC03
            Description
                1. creates an interface with valid ipv6 addresses.
                2. updates the ipv6 value of the interface
                3. Checks that the IPv6 address can be pinged/ ssh into.
                4. Check that ifcfg files are updated correctly
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc08', 'kgb-other')
    def obsolete_08_n_update_interface_ipv6_invalid_addr(self):
        """
        Test merged with
        "test_01_n_create_update_valid_interface_non_mgmt_network"
        #tms_id: litpcds_2064_tc08
        #tms_requirements_id: LITPCDS-2064
        #tms_title: update interface ipv6 to invalid address
        #tms_description: Verify updating interface items ipv6 address
            to invalid value results in a validation error
        #tms_test_steps:
        #step: Create network item under 'infrastructure'
        #result: Item created
        #step: Create eth item on ms, node1 and node2 with ip and ipv6 property
        #result: Items created
        #step: Create and run plan
        #result: Plan executes successfully
        #step: Ping6 ms, node1 and node2
        #result: ms, node1 and node2 are pingable
        #step: Update ipv6address property with invalid value on node1
        #result: error throw: ValidationError
        #result: message shown: is not valid
        #step: update ipv6address property with invalid value on node2
        #result: error throw: ValidationError
        #result: message shown: is not valid
        #step: update ipv6address property with invalid value on ms
        #result: error throw: ValidationError
        #result: message shown: is not valid
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story2064', 'story2064_tc09', 'cdb_priority1')
    def test_09_p_create_update_valid_bridge(self):
        """
        @tms_id: litpcds_2064_tc09
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create update valid bridge
        @tms_description: Verify updating and creating ipv6 property on a
            bridge item results in nodes being pingable, a successful plan
            and information contained in ifcfg is correct
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: Item created
        @step: Create bridge item on ms and node1 with ip4 property and
            ipv6 property
        @result: Items created
        @step: Create network item on ms and node1
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Check multicast_snoop value in ifcfg file
        @result: Multicast_snoop value is set correctly
        @step: Ping ms and node1 on ip6addresses
        @result: Ms and node1 are pingable on ip6addresses
        @step: Ping ms and node1 on ipaddresses
        @result: Ms and node1 are pingable on ipaddresses
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @step: Update ipv6 property on ms and node1
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping ms and node1 on ip6addresses
        @result: Ms and node1 are pingable on ip6addresses
        @step: Ping ms and node1 on ipaddresses
        @result: Ms and node1 are pingable on ipaddresses
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.test_node_if1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(
            self.ms_node, self.ms_url)[0]

        bridge_verify = {}
        vlan_props = []
        # Load network, interface and bridge configs
        bridge_verify[self.ms_url] = data.TEST_09_MS_BRIDGE
        bridge_verify[self.node_urls[0]] = data.TEST_09_NODE1_BRIDGE

        self.log("info", "1. Create bridges and interfaces for test")
        for node, bridge in bridge_verify.iteritems():
            interface = data.TEST_09_INTERFACE
            if node == self.ms_url:
                interface[0]["if_name"] = self.test_ms_if1["NAME"]
                network_props = data.TEST_09_NET_PROPS
            else:
                interface[0]["if_name"] = self.test_node_if1["NAME"]
                network_props = []
            self.data_driven_create(network_props, vlan_props,
                                    bridge, interface, node)

        self.log("info", "2. Create VCS network hosts")
        host_props = data.TEST_09_HOST_PROPS
        for host, props in host_props.iteritems():
            self.create_vcs_net_host(host, props)

        self.log("info", "3. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "4. Check that the multicast_snoop value is being "
                         "set correctly in the ifcfg file")
        for node_url in self.all_node_urls:
            self.chk_multicast_snoop_on_node(node_url, "br_2064")

        self.log("info", "5. Check if bridge is pingable")
        # Ping ip6
        cmd = self.net.get_ping6_cmd("2001:abcd:ef::04", 10, "-I br_2064")
        self.run_command(self.ms_node, cmd, default_asserts=True)

        cmd = self.net.get_ping6_cmd("2001:abcd:ef::05", 10, "-I br_2064")
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        # Ping ip4
        for index, node in enumerate(self.all_nodes, 1):
            cmd = self.net.get_ping_cmd("10.10.10.10" + str(index), 10)
            self.run_command(node, cmd, default_asserts=True)

        self.log("info", "6. Ensure system is configured correctly")
        self._verify_xml_and_ifcfg(bridge_verify)

        self.log("info", "7. Update properties")
        ipv6address = netaddr.IPAddress("2001:cc::8:7")

        for node_url in self.all_node_urls:
            net_if = self.find(
                self.ms_node, node_url, "collection-of-network-interface")[0]
            bridge_url = "{0}/br_2064".format(net_if)
            bridge_props = "ipv6address='{0}'".format(ipv6address)
            self.execute_cli_update_cmd(self.ms_node, bridge_url, bridge_props)
            ipv6address += 1

        self.log("info", "8. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "9. Check if bridge is pingable")
        # Ping ip6
        cmd = self.net.get_ping6_cmd("2001:cc::8:7", 10, "-I br_2064")
        _, _, _ = self.run_command(self.ms_node, cmd)

        cmd = self.net.get_ping6_cmd("2001:cc::8:8", 10, "-I br_2064")
        _, _, _ = self.run_command(self.peer_nodes[0], cmd)

        # Ping ip4
        for index, node in enumerate(self.all_nodes, 1):
            cmd = self.net.get_ping_cmd("10.10.10.10" + str(index), 10)
            self.run_command(node, cmd, default_asserts=True)

        bridge_verify[self.ms_url][0]['ipv6address'] = "2001:cc::8:7"
        bridge_verify[self.node_urls[0]][0]['ipv6address'] = "2001:cc::8:8"

        self.log("info", "10. Ensure system is configured correctly")
        self._verify_xml_and_ifcfg(bridge_verify)

    @attr('all', 'revert', 'story2064', 'story2064_tc10')
    def test_10_n_create_update_bridge_ipv6_only(self):
        """
        @tms_id: litpcds_2064_tc10
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create and update a bridge with ipv6 only
        @tms_description: Verify creating updating bridge items ipv6 address
            results in a successful plan
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: Item created
        @step: Create bridge item on ms and node1 with ipv6 property
        @result: Items created
        @step: Create eth item under 'infrastructure' and node1
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping6 ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat ifcfg" on ms and node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @step: Update ipv6address property with valid value on ms and node1
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping6 ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat ifcfg" on ms and node1 on each eth interface
        @result: Ms and node1 and contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms, node1 and node2 information is correct
        @step: Update ipv6address property with invalid value on ms and node1
        @result:  ValidationError thrown with message 'is not valid'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log("info", "1. Create network, bridge  and interface")
        self.test_node_if1 = self.verify_backup_free_nics(self.ms_node,
                                                          self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.ms_url)[0]

        bridge_verify = {}
        vlan_props = []

        bridge_verify[self.ms_url] = data.TEST_10_MS_BRIDGE
        bridge_verify[self.node_urls[0]] = data.TEST_10_NODE1_BRIDGE

        for node, bridge in bridge_verify.iteritems():
            interface = data.TEST_10_IF
            if node == self.ms_url:
                interface[0]["if_name"] = self.test_ms_if1["NAME"]
                network_props = data.TEST_10_NET_PROPS
            else:
                interface[0]["if_name"] = self.test_node_if1["NAME"]
                network_props = []
            self.data_driven_create(network_props, vlan_props,
                                    bridge, interface, node)

        self.log("info", "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "3. Ensure bridge is pingable")
        cmd = self.net.get_ping6_cmd("2001:abcd:ef::03", 10, "-I br_2064")
        self.run_command(self.ms_node, cmd, default_asserts=True)

        cmd = self.net.get_ping6_cmd("2001:abcd:ef::04", 10, "-I br_2064")
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        self.log("info", "4. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(bridge_verify)

        self.log("info", "5. Update props")
        ipv6address = netaddr.IPAddress("2001:abcd:ef::11")

        for node_url in self.all_node_urls:
            net_if = self.find(
                self.ms_node, node_url, "collection-of-network-interface")[0]
            bridge_url = "{0}/br_2064".format(net_if)
            bridge_props = "ipv6address='{0}'".format(ipv6address)
            self.execute_cli_update_cmd(self.ms_node, bridge_url, bridge_props)
            ipv6address += 1

        self.log("info", "6. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "7. Ensure bridge is pingable")
        cmd = self.net.get_ping6_cmd("2001:abcd:ef::11", 10, "-I br_2064")
        self.run_command(self.ms_node, cmd, default_asserts=True)

        cmd = self.net.get_ping6_cmd("2001:abcd:ef::12", 10, "-I br_2064")
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        bridge_verify[self.ms_url][0]['ipv6address'] = "2001:abcd:ef::11"
        bridge_verify[self.node_urls[0]][0]['ipv6address'] = "2001:abcd:ef::12"

        self.log("info", "8. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(bridge_verify)

        self.log("info", "9. Update ipv6address property with invalid value "
                         "on MS and Node1 this should raise a "
                         "ValidationError.")
        props = "ipv6address='invalid'"
        for url in self.ms_net_url, self.n1_net_url:
            br_url = "{0}/br_2064".format(url)
            self.update_validate_ipv6address_prop(br_url, props, valid=True)

    @attr('all', 'revert', 'story2064', 'story2064_tc11')
    def test_11_n_create_bridge_invalid_ipv6_addr(self):
        """
        @tms_id: litpcds_2064_tc11
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create bridge with an invalid ipv6address
        @tms_description: Verify that a ValidationError is thrown when
            an invalid value is set for the ipv6 address property.
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: item created
        @step: Create bridge item under 'infrastructure' where
        ipv6address='invalid'
        @result: ValidationError thrown with message 'is not valid'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """

        self.log('info', '1. Create network')
        network_url = "{0}/test_network2064".format(self.networks_path)
        props = "name='test1' subnet='10.10.10.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        br_url = "{0}/br_test".format(self.ms_net_url)
        props = "device_name='brtest' network_name='test1' " \
                "ipaddress='10.10.10.10' ipv6address='invalid'"
        self.log('info', '2. Create bridge item on MS with invalid ipv6address'
                         ' value.')
        self.create_iface_and_validate(br_url, props, 'bridge')

    # attr('all', 'revert', '2064')
    def obsolete_12_update_bridge_ipv6_addr(self):
        """
             This test has been merged with TC09
             Description
                1. creates a bridge with valid ipv6 and Ipv4 addresses.
                2. updates the ipv6 value of the bridge
                3. Checks that the IPv6 address can be pinged/ ssh into.
                4. Check that ifcfg files are updated correctly
        """
        pass

    # attr('pre-reg', 'revert', '2064')
    def obsolete_13_update_bridge_ipv6_addr_only(self):
        """
             This test has been merged with TC10
             Description
                1. creates a bridge with valid ipv6 address.
                2. updates the ipv6 value of the bridge
                3. Checks that the IPv6 address can be pinged/ ssh into.
                4. Check that ifcfg files are updated correctly
        """
        pass

    # attr('pre-reg', 'revert', '2064')
    def obsolete_14_n_update_bridge_invalid_ipv6_addr(self):
        """
            Description
                This TC has been merged with TC10
                1. creates a bridge with valid ipv4 and ipv6 address
                2. update the bridge with an invalid ipv6 addr
                3. Checks that the correct error is thrown
        """
        pass

    @attr('all', 'revert', 'story2064', 'story2064_tc15', 'cdb_priority1')
    def test_15_n_create_update_valid_vlan(self):
        """
        @tms_id: litpcds_2064_tc15
        @tms_requirements_id: LITPCDS-2064
        @tms_title: create update valid vlan
        @tms_description: Verify creating and updating vlan item types results
            in a successful plan
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: Item created
        @step: Create second network item under 'infrastructure'
        @result: Item created
        @step: Create vlan item on ms and node1 with ip4 property and
            ipv6 property
        @result: Items created
        @step: Create eth item on ms and node1 with ip4 property and
            ipv6 property
        @result: Items created
        @step: Create 6 vcs-network-host items on node1 with ipv4 value in
            ip property
        @result: Items created
        @step: Create 6 vcs-network-host items on node1 with ipv6 value in
            ip property
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping vlan ipv6 addresses
        @result: Ipv6 addresses are pingable
        @step: Execute cat ifcfg on vlan nodes
        @result: Contents of ifcfg is correct
        @step: Export vlan items
        @result: Xml information is correct
        @step: Update vlan items ipv6 property
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping vlan ipv6 addresses
        @result: Ipv6 addresses are pingable
        @step: Execute cat ifcfg on vlan nodes
        @result: Contents of ifcfg is correct
        @step: Export vlan items
        @result: Xml information is correct
        @step: Update ipv6 property with invalid value on node 1 vlan item
        @result:  ValidationError thrown with message 'is not valid'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.test_node_if1 = self.verify_backup_free_nics(self.ms_node,
                                                          self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.ms_url)[0]
        vlan_verify = {}
        interfaces = {}

        # Load network, vlan and interface configs
        vlan_verify[self.ms_url] = data.TEST_15_MS_VLAN
        vlan_verify[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]
        interfaces[self.ms_url] = data.TEST_15_MS_INTERFACE
        interfaces[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]

        vlan_verify[self.node_urls[0]] = data.TEST_15_NODE1_VLAN
        vlan_verify[self.node_urls[0]][0]["if_name"] = \
                                                self.test_node_if1["NAME"]
        interfaces[self.node_urls[0]] = data.TEST_15_NODE1_INTERFACE
        interfaces[self.node_urls[0]][0]["if_name"] = \
                                                self.test_node_if1["NAME"]

        bridge_props = []
        self.log("info", "1. Create vlans and interfaces for test")
        for node, vlan in vlan_verify.iteritems():
            if node == self.ms_url:
                network_props = data.TEST_15_MS_NET_PROPS
            else:
                network_props = []
            self.data_driven_create(network_props, vlan, bridge_props,
                                    interfaces[node], node)

        net_hosts = data.TEST_15_NET_HOSTS
        self.log("info", "2. Create VCS network hosts")
        for host, props in net_hosts.iteritems():
            self.create_vcs_net_host(host, props)

        self.log("info", "3. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "4. Check if vlan is pingable")
        self._ping_sequential_ip6("2001:abcf:ef::12", vlan=True)

        self.log("info", "5. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(vlan_verify)

        self.log("info", "6. Update properties")
        index = 2064
        ipv6address = netaddr.IPAddress("2001:a2cd:ef::31")

        for node_url in self.all_node_urls:
            net_if = self.find(
                self.ms_node, node_url, "collection-of-network-interface")[0]
            vlan_url = "{0}/vlan_{1}".format(net_if, index)
            vlan_props = "ipv6address='{0}'".format(ipv6address)
            self.execute_cli_update_cmd(self.ms_node, vlan_url, vlan_props)
            ipv6address += 1

        self.log("info", "7. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "8. Check if vlan is pingable")
        self._ping_sequential_ip6("2001:a2cd:ef::31", vlan=True)

        vlan_verify[self.ms_url][0]['ipv6address'] = "2001:a2cd:ef::31"
        vlan_verify[self.node_urls[0]][0]['ipv6address'] = "2001:a2cd:ef::32"

        self.log("info", "9. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(vlan_verify)

        self.log('info', '10. Update ipv6 property with invalid value on Node1'
                         ' vlan item')
        props = "ipv6address='invalid'"
        vlan_url = "{0}/vlan_2064".format(self.n1_net_url)
        self.update_validate_ipv6address_prop(vlan_url, props, valid=True)

    @attr('all', 'revert', 'story2064', 'story2064_tc16')
    def test_16_p_ipv6_to_ipv4_vlan_conversion(self):
        """
        @tms_id: litpcds_2064_tc16
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create update vlan ipv6 only
        @tms_description: Verify creating and updating vlan items from ipv6
            address to ipv4 results in a successful plan
        @tms_test_steps:
        @step: Create network and eth item under 'infrastructure'
        @result: Items created
        @step: Create vlan item on ms and node1 with ipv6 property
        @result: Items created
        @step: Create eth item on ms and node1 with an ip4 and
            ipv6 property
        @result: Items created
        @step: Create 9 cluster level vcs-network-host items
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping6 ms and node1
        @result: Ms and node1 are pingable
        @step: Update ipaddress property and delete ipv6 properties of vlan
            items on node1 and ms
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping ms and node1
        @result: Ms and node1 are pingable
        @step: Execute "cat ifcfg" on ms and node1 on each eth interface
        @result: Ms and node1 contain correct information
        @step: Export network_interfaces item for ms and node1
        @result: Ms and node1 information is correct
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.test_node_if1 = self.verify_backup_free_nics(
            self.ms_node, self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(
            self.ms_node, self.ms_url)[0]

        vlan_verify = {}
        interfaces = {}
        bridge_props = []

        self.log("info", "1. Create network, vlan  and interface")
        vlan_verify[self.ms_url] = data.TEST_16_MS_VLAN
        vlan_verify[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]
        interfaces[self.ms_url] = data.TEST_16_MS_IF
        interfaces[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]

        vlan_verify[self.node_urls[0]] = data.TEST_16_NODE1_VLAN
        vlan_verify[self.node_urls[0]][0]["if_name"] = \
            self.test_node_if1["NAME"]
        interfaces[self.node_urls[0]] = data.TEST_16_NODE1_IF
        interfaces[self.node_urls[0]][0]["if_name"] = \
            self.test_node_if1["NAME"]

        for node, vlan in vlan_verify.iteritems():
            if node == self.ms_url:
                network_props = data.TEST_16_NET_PROPS
            else:
                network_props = []
            self.data_driven_create(network_props, vlan, bridge_props,
                                    interfaces[node], node)

        host_props = data.TEST_16_HOST_PROPS
        for url, prop in host_props.iteritems():
            self.create_vcs_net_host(url, prop)

        self.log("info", "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "3. Check if vlan is pingable")
        cmd = self.net.get_ping6_cmd("2001:abcc:ef:abc:abc:abc:0:12", 10,
                                     "-I {0}.{1}").format(
                                                self.test_ms_if1["NAME"],
                                                self.VLAN1_ID)
        self.run_command(self.ms_node, cmd, default_asserts=True)

        cmd = self.net.get_ping6_cmd("2001:abcc:00ef:0abc::13", 10,
                                     "-I {0}.{1}".format(
                                                self.test_node_if1["NAME"],
                                                self.VLAN1_ID))
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        self.log("info", "4. Update properties")
        index = 2064
        net_url = "{0}/network_{1}".format(self.networks_path, index)
        net_props = "subnet='10.10.10.0/24'"
        self.execute_cli_update_cmd(self.ms_node, net_url, net_props)

        ipaddress = netaddr.IPAddress("10.10.10.54")
        for node_url in self.all_node_urls:
            net_if = self.find(
                self.ms_node, node_url, "collection-of-network-interface")[0]
            vlan_url = "{0}/vlan_{1}".format(net_if, index)
            self.execute_cli_update_cmd(self.ms_node, vlan_url,
                                        "ipv6address", action_del=True)
            vlan_props = "ipaddress='{0}'".format(ipaddress)
            self.execute_cli_update_cmd(self.ms_node, vlan_url, vlan_props)
            ipaddress += 1

        self.log("info", "5. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "6. Check if interface is pingable")
        ipaddress = netaddr.IPAddress("10.10.10.54")
        for node in self.all_nodes:
            cmd = self.net.get_ping_cmd(ipaddress, 10)
            self.run_command(node, cmd, default_asserts=True)
            ipaddress += 1

        vlan_verify[self.ms_url][0]['ipaddress'] = "10.10.10.54"
        vlan_verify[self.node_urls[0]][0]['ipaddress'] = "10.10.10.55"
        vlan_verify[self.ms_url][0]['ipv6address'] = None
        vlan_verify[self.node_urls[0]][0]['ipv6address'] = None

        self.log("info", "7. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(vlan_verify)

    @attr('all', 'revert', 'story2064', 'story2064_tc17')
    def test_17_p_ipv4_to_ipv6_conversion_update(self):
        """
        @tms_id: litpcds_2064_tc17
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Create update vlan ipv6 only
        @tms_description: Verify creating and updating vlan items from ipv4
            address to ipv6 results in a successful plan
        @tms_test_steps:
        @step: Create two network items under 'infrastructure'
        @result: Items created
        @step: Create vlan item on the MS and node1 with ipv4 property
        @result: Items created
        @step: Create eth item on node1 with ipv4 property
        @result: Items created
        @step: Create 9 cluster level vcs-network-host items
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping MS and node1
        @result: MS and node1 are pingable
        @step: Delete subnet property of eth item under "/infrastructure"
        @result: Property removed
        @step: Update ipv6 properties and delete ipv4 properties of vlan
            items on node1 and ms
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping6 MS and node1
        @result: MS and node1 are pingable
        @step: Execute "cat ifcfg" on ms and node1 on each eth interface
        @result: MS and node1 contain correct information
        @step: Export network_interfaces item for MS and node1
        @result: MS and node1 information is correct
        @step: Update ipv6 properties to new values of vlan items on node1,
            and ms
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Ping6 MS and node1
        @result: MS and node1 are pingable
        @step: Execute "cat ifcfg" on MS and node1 on each eth interface
        @result: MS and node1 contain correct information
        @step: Export network_interfaces item for ms, node1 and node2
        @result: MS and node1 information is correct
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.test_node_if1 = self.verify_backup_free_nics(self.ms_node,
                                                          self.node_urls[0])[0]
        self.test_ms_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.ms_url)[0]

        vlan_verify = {}
        interfaces = {}
        bridge_props = []
        self.log("info", "1. Create network, vlan and interfaces for test")
        vlan_verify[self.ms_url] = data.TEST_17_MS_VLAN
        vlan_verify[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]
        interfaces[self.ms_url] = data.TEST_17_MS_IF
        interfaces[self.ms_url][0]["if_name"] = self.test_ms_if1["NAME"]

        vlan_verify[self.node_urls[0]] = data.TEST_17_NODE1_VLAN
        vlan_verify[self.node_urls[0]][0]["if_name"] = \
            self.test_node_if1["NAME"]
        interfaces[self.node_urls[0]] = data.TEST_17_NODE1_IF
        interfaces[self.node_urls[0]][0]["if_name"] = \
            self.test_node_if1["NAME"]

        for node, vlan in vlan_verify.iteritems():
            if node == self.ms_url:
                network_props = data.TEST_17_NET_PROPS
            else:
                network_props = []
            self.data_driven_create(network_props, vlan, bridge_props,
                                    interfaces[node], node)

        host_props = data.TEST_17_HOST_PROPS
        for url, props in host_props.iteritems():
            self.create_vcs_net_host(url, props)

        self.log("info", "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "3. Check if vlan is pingable")
        cmd = self.net.get_ping_cmd('10.10.10.101', 10)
        self.run_command(self.ms_node, cmd, default_asserts=True)

        cmd = self.net.get_ping_cmd('10.10.10.102', 10)
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        self.log("info", "4. Update properties")
        index = 2064
        net_url = "{0}/network_{1}".format(self.networks_path, index)
        self.execute_cli_update_cmd(self.ms_node, net_url,
                                    "subnet", action_del=True)

        urls_and_ips = {self.ms_url: '2001:cc::8:8',
                        self.node_urls[0]: '2001:cc::8:6'}

        for url, ipv6 in urls_and_ips.iteritems():
            net_if = self.find(self.ms_node, url,
                               "collection-of-network-interface")[0]
            vlan_url = "{0}/vlan_{1}".format(net_if, index)
            self.execute_cli_update_cmd(self.ms_node, vlan_url,
                                        "ipaddress", action_del=True)
            vlan_props = "ipv6address='{0}'".format(ipv6)
            self.execute_cli_update_cmd(self.ms_node, vlan_url, vlan_props)

        self.log("info", "5. Create and run plan")
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "6. Check if vlan is pingable")
        if_name = self.test_ms_if1["NAME"]
        cmd = self.net.get_ping6_cmd(urls_and_ips[self.ms_url], 10,
                                     "-I {0}.{1}").format(if_name,
                                                          self.VLAN1_ID)
        self.run_command(self.ms_node, cmd, default_asserts=True)

        if_name = self.test_node_if1["NAME"]
        cmd = self.net.get_ping6_cmd(urls_and_ips[self.node_urls[0]], 10,
                                     "-I {0}.{1}").format(if_name,
                                                          self.VLAN1_ID)
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        vlan_verify[self.ms_url][0]['ipaddress'] = None
        vlan_verify[self.ms_url][0]['ipv6address'] = "2001:cc::8:8"
        vlan_verify[self.node_urls[0]][0]['ipaddress'] = None
        vlan_verify[self.node_urls[0]][0]['ipv6address'] = "2001:cc::8:6"

        self.log("info", "7. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(vlan_verify)

        self.log("info", "8. Update properties")
        index = 2064
        urls_and_ips = {self.ms_url: '2001:abcd:ef::17',
                        self.node_urls[0]: '2001:abcd:ef::15'}

        for url, ipv6 in urls_and_ips.iteritems():
            net_if = self.find(self.ms_node, url,
                               "collection-of-network-interface")[0]
            vlan_url = "{0}/vlan_{1}".format(net_if, index)
            vlan_props = "ipv6address='{0}'".format(ipv6)
            self.execute_cli_update_cmd(self.ms_node, vlan_url, vlan_props)

        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log("info", "9. Check if vlan is pingable")
        if_name = self.test_ms_if1["NAME"]
        cmd = self.net.get_ping6_cmd(urls_and_ips[self.ms_url], 10,
                                     "-I {0}.{1}").format(if_name,
                                                          self.VLAN1_ID)
        self.run_command(self.ms_node, cmd, default_asserts=True)

        if_name = self.test_node_if1["NAME"]
        cmd = self.net.get_ping6_cmd(urls_and_ips[self.node_urls[0]], 10,
                                     "-I {0}.{1}").format(if_name,
                                                          self.VLAN1_ID)
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        vlan_verify[self.ms_url][0]['ipv6address'] = "2001:abcd:ef::17"
        vlan_verify[self.node_urls[0]][0]['ipv6address'] = "2001:abcd:ef::15"

        self.log("info", "10. Check if ifcfg file is correct and xml files "
                         "are valid")
        self._verify_xml_and_ifcfg(vlan_verify)

    @attr('all', 'revert', 'story2064', 'story2064_tc18')
    def test_18_n_create_vlan_invalid_ipv6addr(self):
        """
        @tms_id: litpcds_2064_tc18
        @tms_requirements_id: LITPCDS-2064
        @tms_title: create vlan with invalid ipv6addr property value
        @tms_description: Verify that a ValidationError is thrown when an
                invalid value is given to ipv6 property of a vlan item
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: item created
        @step: Create vlan item on ms with invalid ipv6 address
        @result: error thrown: ValidationError
        @result:  ValidationError thrown with message 'is not valid'
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        free_nics = self.verify_backup_free_nics(self.ms_node, self.ms_url,
                                                 backup_files=False)[0]

        self.log('info', '1. Create network')
        network_url = "{0}/test_network2064".format(self.networks_path)
        props = "name='test' subnet='20.20.20.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

        vlan_url = "{0}/vlan_2064".format(self.ms_net_url)
        props = "device_name='{0}.{1}' network_name='test' " \
                "ipv6address='invalid' ipaddress='20.20.20.22'". \
            format(free_nics["NAME"], self.VLAN1_ID)

        self.log('info', '2.Create vlan item on MS with invalid ipv6address '
                         'value.')
        self.create_iface_and_validate(vlan_url, props, 'vlan')

    # attr('pre-reg', 'revert', '2064')
    def obsolete_19_p_update_vlan_ipv6_addr(self):
        """
             This test has been merged with TC15
             Description
                1. creates a vlan with valid ipv4 and ipv6 address.
                2. updates the ipv6 value of the bridge
                3. Checks that the IPv6 address can be pinged/ ssh into.
                4. Check that ifcfg files are updated correctly
        """
        pass

    # attr('pre-reg', 'revert', '2064')
    def obsolete_20_update_vlan_ipv6_addr_only(self):
        """
             This test has been merged with TC17
             Description
                1. creates a vlan with valid ipv6 address.
                2. updates the ipv6 value of the bridge
                3. Checks that the IPv6 address can be pinged/ ssh into.
                4. Check that ifcfg files are updated correctly
        """
        pass

    # attr('all', 'revert', '2064')
    def obsolete_21_n_update_vlan_invalid_ipv6_addr(self):
        """
            This test has been merged with TC15
            Description
                1. creates a vlan with valid ipv4 and ipv6 address
                2. update the vlan with an invalid ipv6 addr
                3. Checks that the correct error is thrown
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc22', 'kgb-other')
    def obsolete_22_n_validate_prefix(self):
        """
        Obsoleted. Merged with test_24_n_validate_ipaddress_value
        #tms_id: litpcds_2064_tc22
        #tms_requirements_id: LITPCDS-2064
        #tms_title: validate_prefix
        #tms_description: Verify a validation error is thrown when an invalid
        value is given to ipv6 property of an eth item
        #tms_test_steps:
        #step: Create network item under 'infrastructure'
        #result: item created
        #step: Create second network item under 'infrastructure'
        #result: item created
        #step: Create eth item on ms with ipv6address and ipaddress property
        #result: item created
        #step: create and run plan
        #result: plan executes successfully
        #step: Update eth item on ms with invalid ipv6address value
        #result: ValidationError thrown with message 'is not valid'
        #result: item created
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc23', 'kgb-other')
    def obsolete_23_n_validate_address_format(self):
        """
        Obsoleted. Merged with test_24_n_validate_ipaddress_value
        #tms_id: litpcds_2064_tc23
        #tms_requirements_id: LITPCDS-2064
        #tms_title: validate address format
        #tms_description: Verify a validation error is thrown when an invalid
            value is given to ipv6 property of an eth item
        #tms_test_steps:
        #step: Create network item under 'infrastructure'
        #result: item created
        #step: Create second network item under 'infrastructure'
        #result: item created
        #step: Create eth item on ms with ipv6address and ipaddress property
        #result: item created
        #step: create and run plan
        #result: plan executes successfully
        #step: Update eth item on ms with invalid ipv6address value
        #result: ValidationError thrown with message 'is not valid'
        #result: item created
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story2064', 'story2064_tc24')
    def test_24_n_validate_ipaddress_value(self):
        """
        @tms_id: litpcds_2064_tc24
        @tms_requirements_id: LITPCDS-2064
        @tms_title: Validate ipaddress value
        @tms_description: Verify a validation error is thrown when a not
            permitted value is given to ipv6 property of an eth item
        @tms_test_steps:
        @step: Create network item under 'infrastructure'
        @result: item created
        @step: Create second network item under 'infrastructure'
        @result: item created
        @step: Create eth item on ms with ipv6address and ipaddress property
        @result: item created
        @step: create and run plan
        @result: plan executes successfully
        @step: Update eth item on ms with a not permitted ipv6address value
        @result:  ValidationError thrown with message 'is not permitted'
        @result: item created
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        free_nics = self.verify_backup_free_nics(self.ms_node, self.ms_url)[0]

        self.log('info', '1. Create valid network and interface.')
        vlan_props = []
        bridge_props = []
        data.TEST_24_IF_PROPS[0]["if_name"] = free_nics["NAME"]

        self.data_driven_create(
            data.TEST_24_NET_PROPS, vlan_props, bridge_props,
            data.TEST_24_IF_PROPS, self.ms_url)

        self.log('info', '2. Create and Run plan')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 10)

        self.log('info', '3. Update eth item on MS with invalid ipv6address '
                         'values to raise ValidationError "is not valid".')
        if_url = "{0}/if_2064".format(self.ms_net_url)

        properties = ["ipv6address='ffff:a0a:1/0'",
                      "ipv6address='ffff:a0a:1/129'",
                      "ipv6address='ffff:a0a:1/abc'",
                      "ipv6address='ffff:a0a:1/*&^'",
                      "ipv6address='*:0:0:0:0:ffff:a0a:a01/64'",
                      "ipv6address=0:0",
                      "ipv6address=0:0:0:0:0:ghij:a0a:a01/abc"]
        for prop in properties:
            self.update_validate_ipv6address_prop(if_url, prop, valid=True)

        self.log('info', '4. Update eth item on MS with invalid ipv6address '
                         'values to raise ValidationError "is not permitted".')
        properties = ["ipv6address=0:0:0:0:0:0:0:0", "ipv6address=::",
                      "ipv6address=0::", "ipv6address=0:0::",
                      "ipv6address=0::0", "ipv6address=::1",
                      "ipv6address=0::1", "ipv6address=0::1"]

        for prop in properties:
            self.update_validate_ipv6address_prop(if_url, prop)

    # attr('all', 'revert', 'story2064', 'story2064_tc25', 'physical')
    def obsolete_25_p_validate_allowed_address_values(self):
        """
        It was decided this test was no longer needed when it was discovered
        it had not been run since 2015 due to "physical" and "kgb-other" tags
        clashing
        tms_id: litpcds_2064_tc25
        tms_requirements_id: LITPCDS-2064
        tms_title: Validate allowed address values
        tms_description: Verify a validation error is thrown when a not
            permitted value is given to ipv6 property of an eth item
        tms_test_steps:
        step: Update the ip6address property using an address with local scope
        result: Item updated
        step: Create and run plan
        result: Plan executes successfully
        step: Ping6 ms, node1 and node2
        result: Ms, node1 and node2 are pingable
        step: Update the ip6address property using an address with global
            scope
        result: Item updated
        step: Create and run plan
        result: Plan executes successfully
        step: Ping6 ms, node1 and node2
        result: Ms, node1 and node2 are pingable
        tms_test_precondition: NA
        tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc26', 'kgb-other')
    def obsolete_26_n_validate_network_ipv6(self):
        """
        Test converted to AT "test_26_n_validate_network_ipv6.at" in network
        #tms_id: litpcds_2064_tc26
        #tms_requirements_id: LITPCDS-2064
        #tms_title: validate network ipv6
        #tms_description: Verify a validation error is thrown network_name
            prop does not match a defined network
        #tms_test_steps:
        #step: Create eth item on node1 with network_name='test' property
        #result: item created
        #step: create plan
        #result: error thrown: ValidationError
        #result: message shown: network_name "test" does not match a
            defined network.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc27', 'kgb-other')
    def obsolete_27_n_validate_bridge_configured(self):
        """
        Test converted to AT "test_27_n_validate_bridge_configured.at" in
        networkapi
        #tms_id: litpcds_2064_tc27
        #tms_requirements_id: LITPCDS-2064
        #tms_title: validate bridge configured
        #tms_description: Verify a validation error is creating a eth item
        with invalid properties when bridge property is specified
        #tms_test_steps:
        #step: Create bridge item on ms
        #result: item created
        #step: Create eth item with bridge property and invalid properties
        on ms
        #result: error thrown: ValidationError
        #result: message shown: not allowed if "bridge"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc28', 'kgb-other')
    def obsolete_28_p_check_output_flags(self):
        """
        Merged with test_01_n_create_update_valid_interface_non_mgmt_network
        #tms_id: litpcds_2064_tc28
        #tms_requirements_id: LITPCDS-2064
        #tms_title: validate bridge configured
        #tms_description: Verify tentative and dadfailed is not displayed
            after a successful plan to create an eth item
        #tms_test_steps:
        #step: Create network item under "/infrastructure"
        #result: item created
        #step: Create eth item on ms
        #result: item created
        #step: create and run plan
        #result: plan executed successfully
        #step: exccute /sbin/ip -6 addr show on eth item
        #result: tentative and dadfailed is not in output
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc29', 'physical',
    #      'kgb-other')
    def obsolete_29_n_validate_unique_ipaddr_per_node(self):
        """
        Test converted to AT "test_29_n_validate_unique_ipaddr_per_node.at" in
        network
        #tms_id: litpcds_2064_tc29
        #tms_requirements_id: LITPCDS-2064
        #tms_title: validate_unique_ipaddr_per_node
        #tms_description: Verify that create plan fails when attempting to
            make two eth items with identical ipv6 addresses
        #tms_test_steps:
        #step: Create two network items under "/infrastructure"
        #result: items created
        #step: Create two eth items on ms with identical ipv6 addresses
        #result: items created
        #step: create plan
        #result: plan fails to create as IPv6addresses must be unique
        #step: exccute /sbin/ip -6 addr show on eth item
        #result: tentative and dadfailed is not in output
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story2064', 'story2064_tc30', 'kgb-other')
    def obsolete_30_n_create_update_valid_interface_non_mgmt_network(self):
        """
        Test converted to AT
        "test_30_n_create_update_valid_interface_non_mgmt_network" in network
        #tms_id: litpcds_2064_tc30
        #tms_requirements_id: LITPCDS-2064
        #tms_title: create update valid interface non mgmt network
        #tms_description: Verify creating eth items with IPv6 subnet values
        that are different to other nodes on the network results in an error
        being thrown when executing create plan
        #tms_test_steps:
        #step: Create network item under "/infrastructure"
        #result: item created
        #step: Create eth item on ms with IPv6 subnet value thats different
            to other nodes on the network
        #result: item created
        #step: Create eth item on node1 with IPv6 subnet value thats different
            to other nodes on the network
        #result: item created
        #step: Create eth item on node2 with IPv6 subnet value thats different
            to other nodes on the network
        #result: item created
        #step: create plan
        #result: error thrown: ValidationError
        #result: Device on the node attached to the same network is using a
            different IPv6 subnet to other nodes on the network
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass
