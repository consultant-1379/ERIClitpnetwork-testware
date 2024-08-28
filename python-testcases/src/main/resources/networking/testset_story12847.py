"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     February 2016
@author:    Stefan Ulian
@summary:   Integration test for updating eth macaddress property.
Agile:
Story: LITPCDS-12847
"""

from litp_generic_test import GenericTest, attr
from redhat_cmd_utils import RHCmdUtils
import test_constants


class Story12847(GenericTest):
    """
    LITPCDS-12847:
    As a LITP user, I want to be able to support updates to my macaddress on
    my nics so that I can replace faulty blades.
    """

    def setUp(self):
        """
        Runs before every single test
        """
        # 1. Call super class setup
        super(Story12847, self).setUp()

        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filenames()[0]
        self.primary_node = self.get_managed_node_filenames()[0]

        self.ms_url = "/ms"
        self.primary_node_url = self.get_node_url_from_filename(
            self.ms_node, self.primary_node)

        self.rhcmd = RHCmdUtils()

        self.invalid_nic_mac = 'AA:BB:CC:DD:EE:FF'

        self.networks_url_collect = self.find(self.ms_node, "/infrastructure",
                                              "network", False)[0]
        self.ms_net_interface = self.find(self.ms_node, self.ms_url,
                                          'collection-of-network-interface')[0]
        self.n1_net_interface = self.find(self.ms_node, self.primary_node_url,
                                          'collection-of-network-interface')[0]

    def tearDown(self):
        """
        Runs after every single test
        """
        super(Story12847, self).tearDown()

    def check_ifcfg(self, node, nic_name, nic_macaddress, check_puppet=False):
        """
        Description:
            Check eth ifconfig file content has the old/invalid MAC on MS and
            primary node

        Args:
            node (str): Node to execute the command.
            nic_name (str): NIC device name
            nic_macaddress (str): NIC MAC address
        KwArgs:
            check_puppet (boolean) : If set to True, runs check puppet method.
            If False, does not. Default value is False.
        """
        path = "{0}/ifcfg-{1}".format(test_constants.NETWORK_SCRIPTS_DIR,
                                      nic_name)
        dir_contents = self.list_dir_contents(node, path)
        self.assertNotEqual([], dir_contents)
        ifcfg_contents = self.get_file_contents(node, path)
        expected_string = 'HWADDR="{0}"'.format(nic_macaddress)
        error_msg = '{0} not found in the file at {1}'.format(expected_string,
                                                              path)
        self.assertTrue(self.is_text_in_list
                        (expected_string, ifcfg_contents), error_msg)

        if check_puppet:
            self.log('info', 'Check puppet cycle is finished.')
            self.check_puppet_cycle_nic_conf(path, node)

    def update_mac_address(self, node, nic_macaddress, interface_path):
        """
        Description:
            Updates the interface MAC address property with old/invalid
            values

        Args:
            node (str): Node to execute the command.
            nic_macaddress (str): Old/Invalid MAC address
            interface_path (str): Path to network interface on MS and
            primary node
        """
        props = "macaddress='{0}'".format(nic_macaddress)
        self.execute_cli_update_cmd(node, interface_path, props)

    def assert_correct_mac(self, nic_macaddress, interface_path):
        """
        Description:
            Asserts the model has the correct MAC address in the network
            interface

        Args:
            nic_macaddress (str): Old/Invalid MAC address
            interface_path (str): Path to network interface on MS and
            primary node
        """
        self.assertEqual(nic_macaddress, self.get_props_from_url(
            self.ms_node, interface_path, filter_prop='macaddress'))

    def check_puppet_cycle_nic_conf(self, cfg_file, node):
        """
        Description:
        Check Network Interface Configuration(NIC) was restored within
        two puppet cycles.

        Args:
            cfg_file (str): Full path to sysconfig nic file.
            node (str): Node to execute the command.
        """
        self.log('info', 'Rename the nic configuration file.')
        try:
            cmd = self.rhcmd.get_move_cmd(cfg_file, cfg_file + "_old")
            stdout, _, _ = self.run_command(node, cmd,
                                            su_root=True, default_asserts=True)
            self.assertEqual([], stdout)

        finally:
            self.log('info', 'Verify that puppet recreates the file')
            check_file_cmd = '{0} {1}'.format(test_constants.LS_PATH,
                                              cfg_file)
            self.assertTrue(self.wait_for_puppet_action(self.ms_node, node,
                                                        check_file_cmd, 0),
                            "Config file was not restored within 2 Puppet"
                            "cycles")

    @attr('all', 'non-revert', 'story12847', 'story12847_tc01')
    def test_01_pn_update_non_mgmt_eth_mac(self):
        """
        @tms_id: litpcds_12847_tc01
        @tms_requirements_id: LITPCDS-12847
        @tms_title: update non mgmt eth mac address
        @tms_description: To ensure that it is possible to update back the non
                          mgmt eth macaddress property on management server
                          and peer nodes using the old valid value after an
                          invalid update.
        @tms_test_steps:
            @step: Create a new network item.
            @result: Item created.
            @step: Get a free NIC from MS and primary node. Assert there are
                   free NICs.
            @result: NICs retrieved from MS and primary node. Asserted that
                     there are free NICs.
            @step: Create a new interface for the new NIC on MS and primary
                   node.
            @result: Interface created on MS and primary node.
            @step: Add used interfaces to teardown.
            @result: Interfaces added to teardown.
            @step: Create and run the plan.
            @result: Plan executes successfully.
            @step: Update NIC MAC address with invalid values on MS.
            @result: Item updated.
            @step: Create and run the plan.
            @result: Plan fails as expected.
            @step: Check eth ifconfig file content has the invalid MAC on MS.
            @result: File contains correct information.
            @step: Update NIC MAC address with old valid value on MS.
            @result: Item updated.
            @step: Create and run the plan.
            @result: Plan executes successfully.
            @step: Check eth ifconfig file content has the old valid MAC on MS.
            @result: File contains correct information.
            @step: Update NIC MAC address with invalid values on peer node.
            @result: Item updated.
            @step: Create and run the plan.
            @result: Plan fails as expected.
            @step: Check eth ifconfig file content has the invalid NIC on peer
                   node.
            @result: File contains correct information.
            @step: Update NIC MAC address with the old valid value on peer
                   node.
            @result: Item is updated.
            @step: Create and run the plan.
            @result: Plan executes successfully.
            @step: Check eth ifconfig file content has the old valid mac on
                   peer node.
            @result: File contains correct information.
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """

        self.log('info', 'STEP 1. Create a new network item.')
        network_url = self.networks_url_collect + "/test12847"
        props = "name='nodes12847' subnet='50.50.50.0/24'"
        self.execute_cli_create_cmd(self.ms_node, network_url, "network",
                                    props)

        self.log('info', 'STEP 2. Get a free NIC from MS and primary node. '
                         'Assert there are free NICs.')
        free_nic_ms = self.verify_backup_free_nics(self.ms_node,
                                                   self.ms_url)[0]
        free_nic_n1 = self.verify_backup_free_nics(self.ms_node,
                                                   self.primary_node_url)[0]

        self.log('info', 'STEP 3. Create a new interface for the new NIC '
                         'on MS and primary node.')

        interface_url_ms = self.ms_net_interface + '/if12847'
        props = "device_name={0} macaddress='{1}' " \
                "network_name='nodes12847' ipaddress='50.50.50.101'".format(
                    free_nic_ms["NAME"], free_nic_ms["MAC"])
        self.execute_cli_create_cmd(self.ms_node, interface_url_ms, "eth",
                                    props)

        interface_url_n1 = self.n1_net_interface + '/if12847'
        props = "device_name={0} macaddress='{1}' " \
                "network_name='nodes12847' ipaddress='50.50.50.102'".format(
                    free_nic_n1["NAME"], free_nic_n1["MAC"])
        self.execute_cli_create_cmd(self.ms_node, interface_url_n1, "eth",
                                    props)

        self.log('info', 'STEP 4. Add used interfaces to teardown.')
        self.add_nic_to_cleanup(self.ms_node, free_nic_ms['NAME'])
        self.add_nic_to_cleanup(self.primary_node, free_nic_n1['NAME'])

        self.log('info', 'STEP 5. Create and run the plan.')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)

        self.log('info', 'STEP 6. Update NIC MAC address with invalid values '
                         'on MS.')
        self.update_mac_address(self.ms_node, self.invalid_nic_mac,
                                interface_url_ms)

        self.log('info', 'STEP 7. Create and run the plan.')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_FAILED, 20)
        self.assert_correct_mac(self.invalid_nic_mac, interface_url_ms)

        self.log('info', 'STEP 8. Check eth ifconfig file content has the '
                         'invalid MAC on MS.')
        self.check_ifcfg(self.ms_node, free_nic_ms['NAME'],
                         self.invalid_nic_mac,
                         check_puppet=True)

        self.log('info', 'STEP 9. Update NIC MAC address with the old valid '
                         'value on MS.')
        self.update_mac_address(self.ms_node, free_nic_ms['MAC'],
                                interface_url_ms)

        self.log('info', 'STEP 10. Create and run the plan')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)
        self.assert_correct_mac(free_nic_ms['MAC'], interface_url_ms)

        self.log('info', 'STEP 11. Check eth ifconfig file content has the old'
                         ' valid MAC on MS.')
        self.check_ifcfg(self.ms_node, free_nic_ms['NAME'], free_nic_ms['MAC'])

        self.log('info', 'STEP 12. Update NIC MAC address with invalid values'
                         ' on peer node.')
        self.update_mac_address(self.ms_node,
                                self.invalid_nic_mac,
                                interface_url_n1)

        self.log('info', 'STEP 13. Create and run the plan')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_FAILED, 20)
        self.assert_correct_mac(self.invalid_nic_mac, interface_url_n1)

        self.log('info', 'STEP 14. Check eth ifconfig file content has the '
                         'invalid NIC on peer node.')
        self.check_ifcfg(self.primary_node,
                         free_nic_n1['NAME'],
                         self.invalid_nic_mac,
                         check_puppet=True)

        self.log('info', 'STEP 15. Update NIC MAC address with the old valid '
                         'value on peer node.')
        self.update_mac_address(self.ms_node, free_nic_n1['MAC'],
                                interface_url_n1)

        self.log('info', 'STEP 16. Create and run the plan')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE, 20)
        self.assert_correct_mac(free_nic_n1['MAC'], interface_url_n1)

        self.log('info', 'STEP 17. Check eth ifconfig file content has the old'
                         ' valid mac on peer node')
        self.check_ifcfg(self.primary_node, free_nic_n1['NAME'],
                         free_nic_n1['MAC'])
