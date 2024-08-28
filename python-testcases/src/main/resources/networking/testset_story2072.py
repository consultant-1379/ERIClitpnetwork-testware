"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     June 2014
@author:    Gabor Szabo
@summary:   Integration
            Agile: STORY-2072
"""

import netaddr
from xml_utils import XMLUtils
import test_constants as const
import network_test_data as data
from litp_generic_test import GenericTest, attr


class Story2072(GenericTest):
    """
    As a LITP User, I want to configure network interfaces with IEEE 802.1q
    VLAN tags, so that I can have secure and scalable network management
    """
    test_node_if1 = None
    test_node_if2 = None
    VLAN1_ID = 72
    VLAN2_ID = 73

    def setUp(self):
        """
        Runs before every single test
        """
        # 1. Call super class setup
        super(Story2072, self).setUp()

        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()

        self.ms_path = "/ms"
        self.node_paths = self.find(self.ms_node, "/deployments", "node")
        self.all_paths = self.node_paths + [self.ms_path]

        self.ms_net_url = self.find(self.ms_node, self.ms_path,
                                    'collection-of-network-interface')[0]
        self.networks_path = self.find(self.ms_node, "/infrastructure",
                                                        "network", False)[0]
        self.xml = XMLUtils()

    def tearDown(self):
        """
        Description:
            Run after each test and performs the following:
        Actions:
            1. Call the superclass teardown method
            2. Cleanup after test if global results value has been used
        Results:
            Items used in the test are cleaned up and the
            super class prints out end test diagnostics
        """
        # 1. call teardown
        super(Story2072, self).tearDown()

        # This must be done in teardown due to the way LITP handles the removal
        # of nics
        node_if_list = [
            self.test_node_if1,
            self.test_node_if2
        ]

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
        ip_delete = "{0} link del {1}.{2}".format(const.IP_PATH,
                                            if_name,
                                            self.VLAN1_ID)
        ifdown = "{0} {1}".format(const.IFDOWN_PATH,
                                            if_name)
        self.run_command(node, ip_delete, su_root=True, default_asserts=True)
        self.run_command(node, ifdown, su_root=True, default_asserts=True)

        ifcfg_file = "{0}/ifcfg-{1}.{2}".format(
                                        const.NETWORK_SCRIPTS_DIR,
                                        if_name,
                                        self.VLAN1_ID)
        self.remove_item(node, ifcfg_file, su_root=True)

    def create_network_item(self, networks_path, network_props, first_item):
        """
        Description:
            Creates the network item in the LITP model.
        Args:
            networks_path(str): Path to the collection of networks
            network_props(str): Properties for the network item to be created
            first_item(int): A unique number that is incremented for each item
                and appended to the name to ensure each name is unique
        """
        for index, network_prop in enumerate(network_props, first_item):
            network_url = "{0}/network_{1}".format(networks_path, index)
            props = "name='{0}'".format(network_prop["name"])

            if network_prop["subnet"] is not None:
                props += " subnet='{0}'".format(network_prop["subnet"])

            self.execute_cli_create_cmd(self.ms_node, network_url, "network",
                                                                        props)

    def data_driven_create(self, network_props, vlan_props,
                                interface_props, node_urls, first_item=2072):
        """
        Description:
            Build up data model with various input
        Args:
            network_props (list): network input properties
            vlan_props (list): vlan input properties
            interface_props (list): interface input properties
            node_urls (list): all nodes to be configured
        KwArgs:
            first_item(int): Number used to make sure all items created in
                litp model are unique
        """
        self.create_network_item(self.networks_path, network_props, first_item)

        for index, vlan_prop in enumerate(vlan_props, first_item):
            vlan_ip = vlan_prop["ipaddress"]
            if vlan_ip is not None:
                ipaddress = netaddr.IPAddress(vlan_ip)
            for node_url in node_urls:
                vlan_url = "{0}/network_interfaces/vlan_{1}".format(node_url,
                                                                        index)
                props = "device_name='{0}.{1}' network_name='{2}'".format(
                                                    vlan_prop["if_name"],
                                                    vlan_prop["vlan_id"],
                                                    vlan_prop["network_name"])
                if vlan_ip is not None:
                    ipaddress += 1
                    props += " ipaddress='{0}'".format(ipaddress)
                self.execute_cli_create_cmd(self.ms_node, vlan_url, "vlan",
                                                                        props)

        for index, interface_prop in enumerate(interface_props, first_item):
            interface_ip = interface_prop["ipaddress"]
            if interface_ip is not None:
                ipaddress = netaddr.IPAddress(interface_ip)
            for node_url in node_urls:
                all_nics = self.get_all_nics_from_node(self.ms_node, node_url)

                macaddress = None
                for nic in all_nics:
                    if nic["NAME"] == interface_prop["if_name"]:
                        macaddress = nic["MAC"]
                        break

                if_url = "{0}/network_interfaces/if_{1}".format(node_url,
                                                                        index)
                props = "device_name='{0}' macaddress={1} network_name='{2}'".\
                                            format(interface_prop["if_name"],
                                            macaddress,
                                            interface_prop["network_name"])
                if interface_ip is not None:
                    ipaddress += 1
                    props += " ipaddress='{0}'".format(ipaddress)
                self.execute_cli_create_cmd(self.ms_node, if_url, "eth", props)

        file_path = "xml_expected_story2072.xml"

        for node_url in node_urls:
            network_url = "{0}/network_interfaces".format(node_url)
            self.execute_cli_export_cmd(self.ms_node, network_url, file_path)

        cmd = self.xml.get_validate_xml_file_cmd(file_path)
        stdout = self.run_command(self.ms_node, cmd, default_asserts=True)[0]
        self.assertNotEqual([], stdout)

    def check_ifcfg_vlan_props(self, vlan_props, node_urls):
        """
        Description:
            Check system configuration, ensures vlan config files contain
            correct information
        Args:
            vlan_props (list): List of dicts of props of vlan item in model
            node_urls (list): Nodes to be checked
        Results:
            (list) stderr of checking configuration
        """
        errors = []

        for vlan_prop in vlan_props:
            ipaddress = None
            vlan = "{0}.{1}".format(vlan_prop["if_name"], vlan_prop["vlan_id"])
            if vlan_prop["ipaddress"] is not None:
                ipaddress = netaddr.IPAddress(vlan_prop["ipaddress"])

            for node_url in node_urls:
                self.log("info", "VERIFYING NODE {0}".format(node_url))
                node_fname = self.get_node_filename_from_url(self.ms_node,
                                                                    node_url)

                # CHECK VLAN CONFIG FILE EXISTS
                path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR, vlan)
                dir_contents = self.list_dir_contents(node_fname, path)
                if not dir_contents:
                    errors.append("ifcfg-{0} doesn't exist".format(vlan))

                # CHECK VLAN FILE CONTENT
                std_out = self.get_file_contents(node_fname, path)

                device = 'DEVICE="{0}"'.format(vlan)
                device_in_file = self.is_text_in_list(device, std_out)

                if not device_in_file:
                    errors.append("{0} is not configured".format(device))

                if ipaddress is not None:
                    ipaddress += 1
                    ip_string = 'IPADDR="{0}"'.format(ipaddress)
                    if not self.is_text_in_list(ip_string, std_out):
                        errors.append("{0} is not configured".format(
                                                                    ip_string))

                if not self.is_text_in_list('BOOTPROTO="static"', std_out):
                    errors.append('BOOTPROTO="static" is not configured')

                if not self.is_text_in_list('VLAN="yes"', std_out):
                    errors.append('VLAN="yes" is not configured')

        self.assertEqual([], errors)

        return errors

    def pingtest(self):
        """
        Description:
            Checks all interface and vlan IPs on MS and nodes are pingable
        Results:
            stderr of ping command
        """
        errors = []

        for node_url in self.all_paths:
            node_fname = self.get_node_filename_from_url(self.ms_node,
                                                                    node_url)

            interfaces = self.find(self.ms_node, node_url, "eth",
                                                        assert_not_empty=False)
            vlans = self.find(self.ms_node, node_url, "vlan",
                                                        assert_not_empty=False)

            for interface in interfaces + vlans:
                if_ip = self.get_props_from_url(self.ms_node, interface,
                                                                "ipaddress")
                if if_ip is not None:
                    # CHECK INTERFACE IP IS PINGABLE
                    cmd = self.net.get_ping_cmd(if_ip, 10)
                    _, _, ret_code = self.run_command(node_fname, cmd)
                    if ret_code != 0:
                        errors.append("{0} IP is not pingable from node {1}".
                                      format(if_ip, node_fname))

        self.assertEqual([], errors)

        return errors

    #@attr('all', 'revert', 'story2072', 'story2072_tc01')
    def obsolete_01_p_create_vlan1_eth1_ms(self):
        """
        Description:
            This test has been merged with TC05
            Test vlan tagging on 1 network interface where vlan has IP address
            z.z.z.z and interface has x.x.x.x
            create and run plan
            check the vlan interface is configured (ifcfg-nic.vlan)
            and state is up
            check both IPs are contactable
            export vlan into an xml file
            Check xml dump is correct
        """
        pass

    # @attr('all', 'revert', '2072')
    def obsolete_02_p_create_vlan1_eth1_no_ipaddress_mn(self):
        """
        This test has been merged with TC06
        Description:
            Test vlan tagging on 1 network interface where vlan has no
            IP address (ipaddress is optional)
            create and run plan
            check the vlan interface is configured (ifcfg-nic.vlan)
            and state is up
            export vlan into an xml file
            Check xml dump is correct
        """
        pass

    #@attr('all', 'revert', 'story2072', 'story2072_tc03')
    def obsolete_03_p_create_vlan2_eth2_diff_net_if(self):
        """
        Description:
            Test creating of 2 separate vlan tags on 2 different network
            interfaces
            create and run plan
            check the vlan interface is configured (ifcfg-nic.vlan)
            and state is up
            check all configured IPs are contactable
            export vlan into an xml file
            Check xml dump is correct
        """
        pass

    @attr('all', 'revert', 'story2072', 'story2072_tc04')
    def test_04_p_create_vlan2_eth1_same_net_if(self):
        """
        @tms_id: litpcds_2072_tc04
        @tms_requirements_id: LITPCDS-2072
        @tms_title: Create vlans
        @tms_description: Verify creating vlans results in a successful plan
        @tms_test_steps:
        @step: Create three network items under "infrastructure"
        @result: Items created
        @step: Create two vlan items node1 and node2
        @result: Items created
        @step: Create eth items on node1 and node2
        @result: Items created
        @step: Export nodes vlan items
        @result: Items exported
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute ifcfg-bond on ms
        @result: Bond is configured correctly
        @step: Ping vlans and interfaces
        @result: Vlans and interfaces are pingable
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.test_node_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.node_paths[0])[0]

        self.log('info', "1. Create network, interface and vlans for test")
        network_props = data.TEST04_NET_PROPS

        vlan_props = [
            {
                "ipaddress": "10.10.10.100",
                "network_name": "test1",
                "if_name": self.test_node_if1["NAME"],
                "vlan_id": self.VLAN1_ID
            },
            {
                "ipaddress": "30.30.30.100",
                "network_name": "test3",
                "if_name": self.test_node_if1["NAME"],
                "vlan_id": self.VLAN2_ID
            }
        ]

        interface_props = [
            {
                "ipaddress": "20.20.20.100",
                "network_name": "test2",
                "if_name": self.test_node_if1["NAME"]
            }
        ]

        self.data_driven_create(network_props, vlan_props,
                                         interface_props, self.node_paths)

        self.log('info', "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_TASKS_SUCCESS, 10)

        self.log('info', "3. Ensure vlans are configured correctly")
        self.check_ifcfg_vlan_props(vlan_props, self.node_paths)

        self.log('info', "4. Ensure interfaces and vlans are pingable")
        self.pingtest()

    #@attr('all', 'revert', 'story2072', 'story2072_tc05', 'cdb_priority1')
    def obsolete_05_p_update_vlan1_eth1(self):
        """
        Test converted to AT "test_05_p_update_vlan1_eth1.at" in network
        #tms_id: litpcds_2072_tc05
        #tms_requirements_id: LITPCDS-2072
        #tms_title: Create vlans
        #tms_description: Verify creating and updateing vlans results in a
            successful plan
        #tms_test_steps:
        #step: Create two network items under "infrastructure"
        #result: Items created
        #step: Create two vlan items on node1 and node2
        #result: Items created
        #step: Create two eth items on node1 and node2
        #result: Items created
        #step: Export nodes vlan items
        #result: Items exported
        #step: Create and run plan
        #result: Plan executes successfully
        #step: Update two vlan items on node1 and node2
        #result: Items updated
        #step: Create plan
        #result: Create plan executes successfully
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story2072', 'story2072_tc06')
    def test_06_p_create_update_vlan1_eth1_no_ipaddress(self):
        """
        @tms_id: litpcds_2072_tc06
        @tms_requirements_id: LITPCDS-2072
        @tms_title: Create and update vlan and eth items with no ipaddress
            results in a successful plan
        @tms_description: Verify create and update vlan and eth items
            with no ipaddress results in a successful plan
        @tms_test_steps:
        @step: Create two network items under "infrastructure"
        @result: Items created
        @step: Create one vlan item with no ipaddress property
            on node1 and node2
        @result: Items created
        @step: Create one eth items on node1 and node2
        @result: Items created
        @step: Export nodes eth items
        @result: Items exported
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Update two vlan items on node1 and node2 with ipaddress property
        @result: Items updated
        @step: Create plan
        @result: Create plan executes successfully
        @step: Ping nodes vlans
        @result: Vlans pingable
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.test_node_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.node_paths[0])[0]

        self.log('info', "1. Create network, interface and vlans for test")
        network_props = data.TEST06_NET_PROPS

        vlan_props = [
            {
                "ipaddress": None,
                "network_name": "test1",
                "if_name": self.test_node_if1["NAME"],
                "vlan_id": self.VLAN1_ID
            }
        ]

        interface_props = [
            {
                "ipaddress": None,
                "network_name": "test2",
                "if_name": self.test_node_if1["NAME"]
            }
        ]

        self.data_driven_create(network_props, vlan_props,
                                         interface_props, self.node_paths)

        self.log('info', "2. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_TASKS_SUCCESS, 10)

        self.log('info', "3. Update network to add subnet")
        network_url = self.networks_path + "/network_2072"
        network_props[0]["subnet"] = "10.10.10.0/24"
        props = "subnet='{0}'".format(network_props[0]["subnet"])
        self.execute_cli_update_cmd(self.ms_node, network_url, props)

        self.log('info', "4. Update vlan IP address")
        vlan_props[0]["ipaddress"] = "10.10.10.200"
        ipaddress = netaddr.IPAddress(vlan_props[0]["ipaddress"])
        for node_url in self.node_paths:
            # UPDATE VLAN IPADDRESS
            vlan_url = "{0}/network_interfaces/vlan_2072".format(node_url)
            ipaddress += 1
            props = " ipaddress='{0}'".format(ipaddress)
            self.execute_cli_update_cmd(self.ms_node, vlan_url, props)

        self.log('info', "5. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_TASKS_SUCCESS, 10)

        self.log('info', "6. Ensure vlans are configured correctly")
        self.check_ifcfg_vlan_props(vlan_props, self.node_paths)

        self.log('info', "7. Ensure interfaces and vlans are pingable")
        self.pingtest()

    #@attr('all', 'revert', 'story2072', 'story2072_tc07')
    def obsolete_07_n_create_vlan1_bridge1_eth1(self):
        """
        This test is obsolete due to functionality delivered in LITPCDS-6629
        Description:
            Test vlan tagging of 1 bridge interface on 1 network interface
            create a plan
            check getting correct validation error
            (vlan tagging on bridge is not supported)
        """
        pass

    #@attr('all', 'revert', 'story2072', 'story2072_tc08')
    def obsolete_08_n_create_vlan1_eth1_bridge1_eth1(self):
        """
        This test is obsolete due to functionality delivered in LITPCDS-6629
        Description:
            Test vlan tagging of the same network interface
            what is already bridged
            create a plan
            check getting correct validation error
            (vlan tagging and bridge on the same interface is not supported)
        """
        pass

    #@attr('all', 'revert', 'story2072', 'story2072_tc09')
    def obsolete_09_n_create_vlan1_no_net_if(self):
        """
        Test converted to AT "test_09_n_create_vlan1_no_net_if.at" in network
        #tms_id: litpcds_2072_tc09
        #tms_requirements_id: LITPCDS-2072
        #tms_title: create vlan with non existent network
        #tms_description: Verify creating a vlan with where an eth
            doesn't exist reslts in a validation error
        #tms_test_steps:
        #step: Create one network items under "infrastructure"
        #result: item created
        #step: Create one vlan item on ms where a non existent
            device_name property value
        #result: items created
        #step: export item
        #result: item exported
        #step: create plan
        #result: error thrown: ValidationError
        #result: message shown: Invalid VLAN device_name: unknown network
            interface item
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story2072', 'story2072_tc11')
    def test_11_n_validation_vlan_macaddress(self):
        """
        @tms_id: litpcds_2072_tc11
        @tms_requirements_id: LITPCDS-2072
        @tms_title: validation on vlan macaddress property
        @tms_description: Verify creating a vlan with an invalid property
            results in a PropertyNotAllowedError error
        @tms_test_steps:
        @step: Create 1 vlan item on ms with invalid macaddress property
        @result: error thrown: PropertyNotAllowedError
        @result: message shown: macaddress is not an allowed property of vlan
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        # CREATE VLAN WITH INVALID ID
        vlan_url = "{0}/vlan_2072".format(self.ms_net_url)
        props = "device_name='eth72.1000' network_name='test' " \
                "macaddress='BB:BB:BB:BB:BB:BB'"
        std_err = self.execute_cli_create_cmd(
            self.ms_node, vlan_url, "vlan", props, expect_positive=False)[1]

        # Check expected ValidationError is present
        self.assertTrue(self.is_text_in_list("PropertyNotAllowedError",
                                             std_err))

        # Check expected ValidationError is present
        self.assertTrue(self.is_text_in_list("\"macaddress\" is not an allowed"
                                             " property of vlan", std_err))

    #@attr('all', 'revert', 'story2072', 'story2072_tc14')
    def obsolete_14_n_duplicated_device_name_property(self):
        """
        Test converted to AT "test_14_n_duplicated_device_name_property.at" in
            network
        #tms_id: litpcds_2072_tc14
        #tms_requirements_id: LITPCDS-2072
        #tms_title: duplicated device name property
        #tms_description: Verify creating a vlan with an invalid property
            results in a PropertyNotAllowedError error
        #tms_test_steps:
        #step: Create three network items under infrastructure
        #result: items created
        #step: Create two vlan items on ms with the same device_name value
        #result: items created
        #step: Create one eth item on ms
        #result: item created
        #step: export ms network interfaces item
        #result: items exported
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: Interface with device_name is not unique
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    def obsolete_15_n_assign_mgmt_network_to_vlan(self):
        """
        Description:
            Test vlan with the network_name=mgmt property
            create plan
            check getting correct validation error
        """
        pass

    #@attr('all', 'revert', 'story2072', 'story2072_tc16')
    def obsolete_16_n_validate_vlan_mgmt_network_nodes_only(self):
        """
        Converted to AT "test_16_n_validate_vlan_mgmt_network_nodes_only.at"
            in network
        #tms_id: litpcds_2072_tc16
        #tms_requirements_id: LITPCDS-2072
        #tms_title: validate vlan mgmt network nodes only
        #tms_description: Verify creating a vlan on the mgmt
            interface on the peer nodes results in validation error at
            create plan
        #tms_test_steps:
        #step: Create one network items under infrastructure
        #result: items created
        #step: Create one vlan items on node1 with network_name='mgmt'
        #result: item created
        #step: Create one eth item on node1
        #result: item created
        #step: export node1 network interfaces item
        #result: items exported
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: VLAN tagging of the management interface on a
            peer node is not supported
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass
