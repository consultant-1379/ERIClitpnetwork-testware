"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     January 2014
@author:    Kieran Duggan
@summary:   Integration test for creating a bridge for virtual nodes
            to be used
            Agile: STORY-225
"""
from litp_generic_test import GenericTest, attr
from networking_utils import NetworkingUtils
import test_constants as const
from xml_utils import XMLUtils


class Story225(GenericTest):
    """
    As an Administrator I want to create a bridge over a physical interface
    so I can attach virtual nodes to the network
    """

    def setUp(self):
        """
        Runs before every single test
        """
        # 1. Call super class setup
        super(Story225, self).setUp()

        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.ms_url = "/ms"

        self.net = NetworkingUtils()
        self.xml = XMLUtils()

        self.networks_path = self.find(self.ms_node, "/infrastructure",
                                                        "network", False)[0]
        self.ms_net_if = self.find(self.ms_node, self.ms_url,
                                        "collection-of-network-interface")[0]

    def tearDown(self):
        """
        Run after each test and performs the following:
        """
        super(Story225, self).tearDown()

    def find_non_configured_interface(self, node, test_interfaces):
        """
        Description:
            Find a non-configured interface for the test
        Args:
            node (str): node filename
            test_interfaces (list): NICs which already selected for test
        Results:
            (dict) a non-configured interface dictionary. If none exists then
            None will be returned
        """
        # GET ALL INTERFACES
        get_all_nics_cmd = self.net.get_node_nic_interfaces_cmd(False)
        all_nics_ls, _, returnc = self.run_command(node, get_all_nics_cmd)
        self.assertEqual(0, returnc)

        # GET CONFIGURED INTERFACES
        get_nics_cmd = self.net.get_node_nic_interfaces_cmd(True)
        nics_ls, _, returnc = self.run_command(node, get_nics_cmd)
        self.assertEqual(0, returnc)

        # GET INTERFACE MACS FROM THE MODEL
        macs_in_model = self.get_all_macs_in_model(self.ms_node)

        # IS THERE ANY FREE NIC?
        if set(all_nics_ls) == set(nics_ls):
            return None

        # GET ONE OF THE FREE
        free_nics_set = set(all_nics_ls) - set(nics_ls)
        self.log("info", "FREE NICS ON {0} = {1}".format(node, free_nics_set))
        while len(free_nics_set) > 0:
            free_nic = free_nics_set.pop()

            # IT HAS NOT BEEN SELECTED YET
            if free_nic not in test_interfaces:
                cmd = self.net.get_ifconfig_cmd(free_nic)
                std_out, _, return_code = self.run_command(node, cmd)
                self.assertEqual(0, return_code)
                interface = self.net.get_ifcfg_dict(std_out, free_nic)

                # CHECK FREE INTERFACE IS CONFIGURED IN THE MODEL
                if not interface["MAC"] in macs_in_model:
                    return interface

        return None

    def export_validate_xml(self, path, file_name):
        """
        Description
            Exports the created item to xml file and validates the xml file
        Args:
            path(str): The litp path to export
            file_name(str): The path to the xml file to be exported to
        """
        self.execute_cli_export_cmd(self.ms_node, path, file_name)

        cmd = self.xml.get_validate_xml_file_cmd(file_name)
        stdout, _, _ = self.run_command(self.ms_node, cmd,
                                                        default_asserts=True)
        self.assertNotEqual(stdout, [])

    def check_file(self, path, props):
        """
        Description:
            Checks whether or not the specified files contains all the
            expected contents
        Args:
            path(str): The path to the file to check
            props(list): List of lines to check for in the file
        """
        dir_contents = self.list_dir_contents(self.ms_node, path)
        self.assertNotEqual([], dir_contents)

        stdout = self.get_file_contents(self.ms_node, path)
        for prop in props:
            self.assertTrue(self.is_text_in_list(prop, stdout))

    def create_network(self, name, subnet, url="test_network225"):
        """
        Description:
            Creates network with the specified props
        Args:
            name(str): The name of the network
            subnet(str): The subnet of the network
        KwArgs:
            url(str): Unique name for the network item in the LITP model.
            Default is "test_network225"
        """
        network_url = self.networks_path + "/" + url
        props = "name='{0}' subnet='{1}'".format(name, subnet)
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", props)

    @attr('all', 'revert', 'story225', 'story225_tc01', 'physical')
    def test_01_p_create_update_bridge_over_single_interface(self):
        """
        @tms_id: litpcds_225_tc01
        @tms_requirements_id: LITPCDS-225
        @tms_title: Create update bridge over single interface
        @tms_description: Verify creating and updating a bridge over a single
            interface is successful
        @tms_test_steps:
        @step: Create eth item under 'infrastructure'
        @result: Item created
        @step: Create eth item on ms
        @result: Item created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Update IPv6 address property on eth item on ms
        @result: Item updated
        @step: Create and run plan
        @result: Plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Setup network for test")
        test_ms_if1 = self.verify_backup_free_nics(self.ms_node,
                                                            self.ms_url)[0]

        net_model_name = "test_network225"
        self.create_network("test", "10.10.10.0/24", net_model_name)
        network_url = self.networks_path + "/" + net_model_name
        self.export_validate_xml(network_url, "xml_story225.xml")

        self.log('info', "2. Setup eth and bridge")
        if_url = self.ms_net_if + "/if225"
        props = "macaddress='{0}' device_name='{1}' bridge='br225'".format(
                                                    test_ms_if1["MAC"],
                                                    test_ms_if1["NAME"])
        self.execute_cli_create_cmd(self.ms_node, if_url, "eth", props)
        self.export_validate_xml(if_url, "xml_story225.xml")

        br_url = self.ms_net_if + "/br225"
        props = "device_name='br225' ipaddress='10.10.10.2' " \
                "forwarding_delay='4' stp='false' network_name='test'"
        self.execute_cli_create_cmd(self.ms_node, br_url, "bridge", props)
        self.export_validate_xml(br_url, "xml_story225.xml")

        try:
            self.log('info', "3. Create and run plan")
            self.run_and_check_plan(self.ms_node, const.PLAN_TASKS_SUCCESS, 10)

            self.log('info', "4. Check ifcfg file")
            path = "{0}/ifcfg-br225".format(const.NETWORK_SCRIPTS_DIR)
            props = [
                'DEVICE="br225"',
                'BOOTPROTO="static"',
                'ONBOOT="yes"',
                'TYPE="Bridge"',
                'IPADDR="10.10.10.2"',
                'NETMASK="255.255.255.0"',
                'BROADCAST="10.10.10.255"',
                'NM_CONTROLLED="no"',
                'BRIDGING_OPTS="multicast_snooping=1 multicast_querier=0'
                ' multicast_router=1 hash_max=512 hash_elasticity=4"',
                'STP="off"',
                'DELAY="4"',
            ]
            self.check_file(path, props)

            self.log('info', "5. Check bridged interface")
            path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                          test_ms_if1["NAME"])
            stdout = self.get_file_contents(self.ms_node, path)
            self.assertTrue(self.is_text_in_list('BRIDGE="br225"', stdout))

            cmd = self.net.get_ifconfig_cmd("br225")
            self.run_command(self.ms_node, cmd, default_asserts=True)

            self.log('info', "6. Add ipv6 to bridge")
            props = "ipv6address=fdda:4a7e:d471::835:105:0100/64"
            self.execute_cli_update_cmd(self.ms_node, br_url, props)

            self.log('info', "7. Create and run plan")
            self.run_and_check_plan(self.ms_node, const.PLAN_TASKS_SUCCESS, 10)

            self.log('info', "8. Check bridge ipv6")
            path = "{0}/ifcfg-br225".format(const.NETWORK_SCRIPTS_DIR)
            stdout = self.get_file_contents(self.ms_node, path)
            self.assertTrue(self.is_text_in_list(
                'IPV6ADDR="fdda:4a7e:d471::835:105:0100/64"', stdout))

            cmd = self.net.get_ping6_cmd("fdda:4a7e:d471::835:105:0100", 2)
            _, _, ret_code = self.run_command(self.ms_node, cmd)
            self.assertEqual(0, ret_code)

            self.log('info', "9. Change bridge name and validate error")
            props = 'device_name="br226"'
            _, stderr, _ = self.execute_cli_update_cmd(self.ms_node,
                                    br_url, props, expect_positive=False)

            self.assertTrue(self.is_text_in_list("InvalidRequestError",
                                                  stderr))
            self.assertTrue(self.is_text_in_list("Unable to modify readonly "
                                                 "property: device_name",
                                                  stderr))
        finally:
            self.log('info', "10. Deconfigure bridge and interface")
            cmd = "{0} br225".format(const.IFDOWN_PATH)
            self.run_command(self.ms_node, cmd, su_root=True)

            cmd = "{0} {1}".format(const.IFDOWN_PATH, test_ms_if1["NAME"])
            self.run_command(self.ms_node, cmd, su_root=True)

    # attr('all', 'revert')
    def obsolete_02_p_create_bridge_over_multiple_interfaces(self):
        """
        TC made obsolete due to outcome of LITPCDS-6463
        Description:
        Create a bridge over multiple interfaces.
        Actions:
            1: create a new network and two interfaces
            2: Assert no errors
            3: create a bridge over both of these interfaces
            4: assert errors
        Result:
            Bridge is created
        """
        pass

    # attr('all', 'revert', '225')
    def obsolete_03_n_update_bridge_property(self):
        """
        Description:
            *This test has been merged with TC01
            Creates a bridge over a interface and creates plan.
            Change bridge interface or IP address or network,
            expects error message
        Actions:
            1: create a new network, interface and bridge
            2: Assert no errors
            3: create plan and assert no errors
            4: change bridge interface, expects error message
            5: change bridge ip address, expects error message
            4: change bridge network, expects error message
        Results:
            correct ValidationError
        """
        pass

    # attr('all', 'revert', 'story225', 'story225_tc04')
    def obsolete_04_n_create_bridge_on_mgmt_network(self):
        """
        This test is obsolete due to functionality delivered in LITPCDS-6629
        Description:
            Create a bridge with network tagged with litp_management=true,
            create plan, expects a ValidationError error message
        Actions:
            1: create a new network, interface and bridge on mgmt network
            2: Assert no errors
            2: create plan and assert ValidationError
        Results:
            correct ValidationError
        """
        pass

    # attr('all', 'revert', 'story225', 'story225_tc05')
    def obsolete_05_n_add_bridge_with_no_interface(self):
        """
        Test converted to "test_05_n_add_bridge_with_no_interface.at" in
            network
        #tms_id: litpcds_225_tc05
        #tms_requirements_id: LITPCDS-225
        #tms_title: create a bridge with no interface
        #tms_description: Verify createing a bridge which doesn't have
            associated interface results in a failed plan
        #tms_test_steps:
        #step: Create network item under 'infrastructure'
        #result: Item created
        #step: Create bridge item on ms
        #result: Item created
        #step: Create and run plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Bridge is not used.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story225', 'story225_tc06')
    def obsolete_06_n_add_linked_interface_with_no_bridge(self):
        """
        Test converted to "test_06_n_add_linked_interface_with_no_bridge.at" in
            network
        #tms_id: litpcds_225_tc06
        #tms_requirements_id: LITPCDS-225
        #tms_title: create a network with no interface
        #tms_description: Verify creating an interface with non-existent bridge
            property value results in an error when running create plan
        #tms_test_steps:
        #step: Create network item under 'infrastructure'
        #result: item created
        #step: Create eth item under on ms with a non-existent bridge property
            value
        #result: item created
        #step: Create plan
        #result: Error thrown: ValidationError
        #result: Message shown:  Create plan failed: Property bridge
            "br225" does not correspond to a valid bridge.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('pre-reg', 'revert', 'story225', 'story225_tc07', 'physical')
    def obsolete_07_n_add_incorrectly_linked_interface(self):
        """
        Converted to AT "test_07_n_add_incorrectly_linked_interface" in network
        #tms_id: litpcds_225_tc07
        #tms_requirements_id: LITPCDS-225
        #tms_title: Add incorrectly linked interface
        #tms_description: Add an interface which is linked to another interface
            instead of a bridge
        #tms_test_steps:
        #step: Create network item under 'infrastructure'
        #result: Item created
        #step: Create eth item under on ms with property bridge='br225'
        #result: Item created
        #step: Create a second eth item under on ms with device_name='br225'
        #result: Item created
        #step: Create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Property bridge
            "br225" does not correspond to a valid bridge.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story225', 'story225_tc08')
    def obsolete_08_n_invalid_bridge(self):
        """
        Test converted to "test_08_n_invalid_bridge.at" in network and
        networkapi
        #tms_id: litpcds_225_tc08
        #tms_requirements_id: LITPCDS-225
        #tms_title: invalid_bridge property and/or values
        #tms_description: Verify creating an item of type bridge with invalid
            propert and/or values results in a validation error either at item
            creating or create plan.
        #tms_test_steps:
        #step: Create network item under 'infrastructure'
        #result: item created
        #step: Create a second network item under 'infrastructure'
        #result: item created
        #step: Create third network item under 'infrastructure'
        #result: item created
        #step: create a bridge item on the ms with no properties defined
        #result: Error thrown: MissingRequiredPropertyError
        #result: Message shown:  ItemType "bridge" is required to have a
            property with name "device_name"
        #result: Message shown:  ItemType "bridge" is required to have a
            property with name "network_name"
        #step: create a bridge item on the ms with invalid device_name value
        #result: Error thrown: ValidationError
        #result: Message shown:  Value must be a valid Bridge device name
        #step: create a second bridge item on the ms with invalid device_name
            value
        #result: Error thrown: ValidationError
        #result: Message shown:  Value must be a valid Bridge device name
        #step: create a third bridge item on the ms with invalid 'macaddress'
            property
        #result: Error thrown: PropertyNotAllowedError
        #result: Message shown: "macaddress" is not an allowed property of
            bridge
        #step: create a fourth bridge item on the ms with invalid 'ipaddress'
            property value
        #result: Error thrown: ValidationError
        #result: Message shown: Invalid IPAddress value
        #step: create a fifth bridge item on the ms with network_name='unknown
            and device_name='br6'
        #result: item created
        #step: execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown:Create plan failed: Property network_name
            "unknown" does not match a defined network
        #result: Message shown:Create plan failed: Bridge "br6" is not used
        #step: create a sixth bridge item on the ms with ipaddress='9.9.9.9'
            and device_name='br7'
        #result: item created
        #step: execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown:Create plan failed: IP address "9.9.9.9" not
            within subnet "10.10.10.0/24" of network "test".
        #result: Message shown:Create plan failed: Bridge "br7" is not used.
        #step: create a seventh bridge item on the ms with
            ipaddress='10.10.10.0' and device_name='br8'
        #result: item created
        #step: execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Cannot assign IPv4
        #result: Message shown:Create plan failed: Bridge "br8" is not used.
        #step: create an eighth bridge item on the ms with
            ipaddress='10.10.10.255' and device_name='br9'
        #result: item created
        #step: execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown:  Create plan failed: Cannot assign IPv4
            address
        #result: Message shown:Create plan failed: Bridge "br9" is not used.
        #step: create bridge item with device_name='br10'
        #result: item created
        #step: create eth item with device_name='br10'
        #result: item created
        #step: create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Interface with
            device_name "br10" is not unique.
        #step: create bridge item with device_name='br11'
        #result: item created
        #step: create eth item with device_name='br11'
        #result: item created
        #step: create another bridge item with device_name='br12'
        #result: item created
        #step: create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Interface with
            device_name "br11" is not unique.
        #step: create bridge item with network_name='test'
        #result: item created
        #step: create another bridge item with network_name='test'
        #result: item created
        #step: create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Network name "test"
            must be used by one network-interface
        #step: create bridge item with ipaddress='20.20.20.15'
        #result: item created
        #step: create another bridge item with ipaddress='20.20.20.15'
        #result: item created
        #step: create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: IP addresses must be
            unique per node.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story225', 'story225_tc09')
    def obsolete_09_n_validate_stp(self):
        """
        Converted to AT "test_09_n_validate_stp.at" in networkapi
        #tms_id: litpcds_225_tc09
        #tms_requirements_id: LITPCDS-225
        #tms_title: Invalid stp value
        #tms_description: Verify validation eror when setting stp property to
            invalid value
        #tms_test_steps:
        #step: Create bridge item with invalid value for stp property
        #result: Error thrown: ValidationError
        #result: Message shown: Invalid value
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'revert', 'story225', 'story225_tc10')
    def obsolete_10_n_validate_forwarding_delay(self):
        """
        Converted to AT "test_10_n_validate_forwarding_delay.at" in networkapi
        #tms_id: litpcds_225_tc10
        #tms_requirements_id: LITPCDS-225
        #tms_title: validate forwarding delay
        #tms_description:  Validate the forwarding_delay
            property(must be between 0-300)
        #tms_test_steps:
        #step: Create a network item under "/infrastructure"
        #result: item created
        #step: Create a bridge item with negative int forwarding_dalay
            property value on ms
        #result: Error thrown: ValidationError
        #result: Message shown: Invalid value
        #step: Create second bridge item with invalid forwarding_dalay
            property value (string)
        #result: Error thrown: ValidationError
        #result: Message shown: Value outside range 0 - 300
        #step: Create third bridge item with invalid forwarding_dalay
            property value (string)
        #result: Error thrown: ValidationError
        #result: Message shown: Invalid value
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass
