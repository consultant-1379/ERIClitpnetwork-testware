"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     January 2014
@author:    Padraic
@summary:   Integration test for model validation framework
            Agile: STORY-091
"""
from litp_generic_test import GenericTest, attr
from networking_utils import NetworkingUtils


class Story91(GenericTest):
    """
    As a LITP user I want to model the network name and nic network elements
    so I can achieve a basic networking configuration of a compute node
    """

    def setUp(self):
        """
        Runs before every single test.
        """
        # 1. Call super class setup
        super(Story91, self).setUp()

        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.node_urls = self.find(self.ms_node, "/deployments", "node")
        self.net = NetworkingUtils()

    def tearDown(self):
        """
        Runs after every single test
        """
        # 1. Cleanup
        super(Story91, self).tearDown()

    #@attr('all', 'revert', 'story91', 'story91_tc01')
    def obsolete_01_n_invalid_node_level_network(self):
        """
        Converted to AT "test_01_n_invalid_node_level_network.at" in network
        Description:
            1. Remove ipaddress property from node1 network interface
            2. Fail to create plan due to interface tied to management network
                requiring an ipv4 address and the route gateway not being
                reachable from any interfaces on the node
            3. Update network name on node1 from "mgmt" to "test" and update
                the ipaddress
            4. Fail to create plan due to management network not being used
                for at least one interface and route gateway not reachable
                from any interfaces on the node
            5. Remove the network interface completely
            6. Fail to create plan due to the collection requiring a minimum
                of one items not marked for removal
        """
        pass

    #@attr('all', 'revert', 'story91', 'story91_tc02')
    def obsolete_02_n_invalid_interface(self):
        """
        Converted to AT "test_02_n_invalid_interface.at" in network
        #tms_id: litpcds_91_tc02
        #tms_requirements_id: LITPCDS-91
        #tms_title: Invalid node level network property values
        #tms_description: Verify errors are thrown when all required
            properties are not set and/or invalid values are given.
        #tms_test_steps:
        #step: Create eth item with missing device_name & macaddress property
        #result: Error thrown: MissingRequiredPropertyError
        #result: Message shown: ItemType "eth" is required to have a property
            with name "macaddress"
        #result: Message shown: ItemType "eth" is required to have a property
            with name "device_name"
        #step: Create eth item with invalid device_name value
        #result: Error thrown: ValidationError
        #result:  Message shown: Value must be a valid generic device name
        #step: Create eth item with invalid macaddress value
        #result: Error thrown: ValidationError
        #result:  Message shown: Invalid value
        #step: Create eth item with invalid ipaddress value
        #result: Error thrown: ValidationError
        #result:  Message shown: Invalid IPAddress value
        #step: Create eth item where network_name="unkmown"
        #result: eth item created
        #step: execute create plan
        #result: Error thrown: ValidationError
        #result:  Message shown: Create plan failed: Property network_name
            "unknown" does not match a defined network.
        #step: Create an interface with an ipaddress outside of the network
            subnet
        #result: Item created
        #step: Create plan
        #result: Fail to create plan due to ipaddress not being within subnet
        #step: Create interface with network ipaddress
        #result: Item created
        #step: Create plan
        #result: Fail to create plan due to not being able to assign ipv4
            address
        #step: Create interface with broadcast ipaddress
        #result: Item created
        #step: Create plan
        #result: Fail to create plan due to not being able to assign ipv4
            address
        #step: Create two test interfaces with the same device name
        #result: Items created
        #step: Create plan
        #result: Fail to create plan due to interface device_names not being
            unique
        #step: Create two test interfaces with the same macaddress
        #result: Items created
        #step: Create plan
        #result: Fail to create plan due to interface macaddresses not being
            unique
        #step: Create two test interfaces with the same network name
        #result: Items created
        #step: Create plan
        #result: Fail to create plan due to interface network name not being
            unique
        #step: Create two test interfaces with the same ipaddress
        #result: Items created
        #step: Create plan
        #result: Fail to create plan due to interface ipaddress not being
            unique per node
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'cdb_tmp', 'story91', 'story91_tc03')
    def obsolete_03_n_invalid_network(self):
        """
        Converted to AT "test_03_n_invalid_network.at" in network
        #tms_id: litpcds_91_tc03
        #tms_requirements_id: LITPCDS-91
        #tms_title: Invalid node level network property
        #tms_description: Verify errors are thrown when mandatory
            properties are not set and/or invalid values are given.
        #tms_test_steps:
        #step: Create eth item under "/infrastructure" with
            missing mandatory properties
        #result: Error thrown: MissingRequiredPropertyError
        #result: Message shown:  ItemType "network" is required to have a
            property with name "name"
        #step: Create eth item under "/infrastructure" with
            litp_management='true'
        #result: item created
        #step: Create another eth item under "/infrastructure" with
            litp_management='true'
        #result: Item created
        #step: Execute create plan
        #result: Error thrown: ValidationError
        #result:  Message shown:  Create plan failed: There must be exactly
            one network assigned litp_management="true"
        #step: Create eth item under "/infrastructure" with name='test'
        #result: Item created
        #step: Create another eth item under "/infrastructure" with name="test"
        #result: Item created
        #step: Execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown:  Create plan failed: Network name "test"
            is not unique.
        #step: Create eth item under "/infrastructure" with invalid subnet
            value
        #result: Error thrown: ValidationError
        #result:Message shown:  Invalid IPv4 subnet value
        #step: Create another eth item under "/infrastructure" with invalid
            subnet value
        #result: Error thrown: ValidationError
        #result: Message shown: Invalid IPv4 subnet value
        #step: Create eth item on node1
        #result: eth item created
        #step: Create and run plan
        #result: Plan is successful
        #step: Remove eth item under '/infrastructure'
        #result: Item set to state ForRemoval
        #step: Execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Property network_name
            does not match a defined network
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story91', 'story91_tc04', 'cdb_priority1')
    def test_04_p_check_network_config(self):
        """
        @tms_id: litpcds_91_tc04
        @tms_requirements_id: LITPCDS-91
        @tms_title: check network config
        @tms_description: Verify the LITP model network details for each node
        match output from ifconfig
        @tms_test_steps:
        @step: Retrieve network information defined in LITP model for node
        @result: Information retrieved
        @step: Ensure hostname on node matches hostname in model
        @result: Hostnames match
        @step: Run ifconfig on node
        @result: Ifconfig output retrieved
        @step: Assert nic, mac and IP address info matches what is defined
            in the model
        @result: Information on node matches what is in model
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        for node_url in self.node_urls:
            self.log('info',
                "1. Retrieve network info defined in LITP model for node")
            net_dict = self.get_node_net_from_tree(self.ms_node, node_url)
            hostname = net_dict[self.hostname_key]
            ip_adds = net_dict[self.ips_key]
            nic_mac_pairs = net_dict[self.interface_mac_key]
            self.log("info", "NODE NIC MAC PAIR={0}".format(nic_mac_pairs))

            self.assertTrue(hostname,
                            "Node hostname could not be found in the model")
            self.assertNotEqual([], ip_adds)
            self.assertNotEqual([], nic_mac_pairs)

            self.log('info',
                "2. Check hostname reported on node matches hostname in model")
            node = self.get_node_filename_from_url(self.ms_node, node_url)
            self.assertNotEqual(None, node)

            stdout = self.run_command(node, "hostname",
                                      default_asserts=True)[0]
            self.assertTrue(self.is_text_in_list(hostname, stdout),
                            "Hostname defined in model not present on node")

            self.log('info', "3. Run ifconfig on node")
            if_config_cmd = self.net.get_ifconfig_cmd()
            stdout = self.run_command(node, if_config_cmd,
                                      default_asserts=True)[0]

            self.log('info', '4. Assert ifconfig contains same NIC name, MAC'
                             'and IP as defined in the model.')
            macs_in_model = self.get_all_macs_in_model(self.ms_node)
            for item in nic_mac_pairs:
                macaddress = item['macaddress']
                if_name = item['interface_name']
                if macaddress in macs_in_model:
                    if_config_dict = self.net.get_ifcfg_dict(stdout, if_name)

                    self.assertFalse(if_config_dict is None,
                                    "Interface {0} is not present on node {1}"
                                        .format(if_name, node))

                    self.assertEqual(
                        self.net.get_mac_from_dict(if_config_dict).lower(),
                        macaddress.lower()
                    )

                    ipv4 = if_config_dict[self.net.dict_key_ipv4]
                    if ipv4 is not None:
                        self.assertTrue(self.is_text_in_list(
                            self.net.get_ipv4_from_dict(if_config_dict),
                            ip_adds),
                            "IP address found which is not in LITP model"
                            "Node: {0} IP: {1}".format(node, ipv4))
