"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     June 2017
@author:    Paul Carroll
@summary:   Integration
            Agile: TORF-196696
"""
import re
import test_constants
from litp_generic_test import GenericTest, attr


class Story196696(GenericTest):
    """
    ENM streaming applications need to be able to configure the interface
    transmission queue size (txqueuelen) on racks running streaming
    applications. In order to do this, the LITP Networking plugin should be
    updated to have a new optional parameter (txqueuelen) that will allow us
    to model this value. If the value is not modelled, LITP should not set
    a default.

    ENM streaming applications need to be able to configure the bonds transmit
    hash policy (xmit_hash_policy) on racks running streaming applications. In
    order to do this, the LITP Networking plugin should be updated to have a
    new optional parameter (xmit_hash_policy) that will allow us to model this
    value. If the value is not modelled, LITP should not set a default.
    """

    def setUp(self):
        """
        Runs before every single test.
        """
        super(Story196696, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()

        self.networks_path = self.find(self.ms_node, '/infrastructure',
                                       'network', False)[0]

        self.node_urls = self.find(self.ms_node, '/deployments', 'node')
        self.mn_net_url = self.find(
            self.ms_node, '/deployments', 'collection-of-network-interface')

        self.n1_nics = self._get_required_nics(self.node_urls[0])
        self.n2_nics = self._get_required_nics(self.node_urls[1])

        self.test_network_name = 'net196696'
        self.test_network_subnet = '25.25.25.'
        self.test_network_cidr = self.test_network_subnet + '0/24'
        self.test_address_n1 = self.test_network_subnet + '1'
        self.test_address_n2 = self.test_network_subnet + '2'
        self.test_network_url = self.networks_path + '/{0}'.format(
            self.test_network_name)

        self.bond_name = 'bond196696'
        self.bond_mode = '4'
        self.bond_initial_xmit_policy = 'layer3+4'
        self.bond_updated_xmit_policy = 'layer2'

        self.initial_txqueuelen_value = '999'
        self.updated_txqueuelen_value = '995'

        self.restore_values = {self.peer_nodes[0]: {},
                               self.peer_nodes[1]: {}, }

        for nic in self.n1_nics:
            name = nic['NAME']
            host = self.peer_nodes[0]
            self.restore_values[host][name] = self._get_txqueuelen(host, name)
        for nic in self.n2_nics:
            name = nic['NAME']
            host = self.peer_nodes[1]
            self.restore_values[host][name] = self._get_txqueuelen(host, name)

    def tearDown(self):
        """
        Runs after every single test.
        """
        super(Story196696, self).tearDown()

        cmd = '{0} "-{1}" > /sys/class/net/bonding_masters'.format(
                            test_constants.ECHO_PATH,
                            self.bond_name)
        for host in self.peer_nodes:
            self.run_command(host, cmd, su_root=True)

        # Restore the original txqueuelen value for re-runs of the same test
        for host, nictxql in self.restore_values.items():
            for nic, value in nictxql.items():
                ifcfg_cmd = '{0} txqueuelen {1}'.format(
                        self.net.get_ifconfig_cmd(nic), value)
                self.run_command(host, ifcfg_cmd, su_root=True)

    def _get_required_nics(self, node_path):
        """
        Description: As long as they are free return specific NICs that are
                     connected to the same vApp.
        Args:
            node_path (str): Model path of the node.

        Returns (list): Two NICS on the 'Services' vApp network.
        """
        target_nics = []
        all_free = self.get_free_nics_on_node(self.ms_node, node_path)
        for _nic in all_free:
            if _nic['NAME'] in ['eth1', 'eth9']:
                target_nics.append(_nic)
        return target_nics

    def _get_txqueuelen(self, hostname, nic):
        """
        Returns txqueuelen value of an eth interface on a node.

        Args:
            hostname (str): Hostname of the node the eth device is on.
            nic (str)     : The eth device name.

        Returns:
            txqueuelen current set on the physical eth device.
        """
        cmd = self.net.get_ifconfig_cmd(ifc_args=nic)
        stdout, _, _ = self.run_command(hostname, cmd, default_asserts=True)
        applied_value = None
        for _line in stdout:
            _match = re.match('.*txqueuelen ([0-9]+)', _line)
            if _match:
                applied_value = _match.group(1)
        return applied_value

    def _model_bond(self, node_path, slave_nics, address, hostname):
        """
        Models LITP bond and eth items on a node.

        Args:
            node_path (str) : Model path of the LITP node.
            slave_nics (list): List of nics to create a slave devices.
            address (str)    : The IPv4 address to assign to the bond.
            hostname (str)   : The hostname of the LITP node.
        """
        eth_props_template = 'device_name={0} macaddress={1} master={2} ' \
                             'txqueuelen={3}'

        bond_props_template = 'device_name={device_name} ' \
                              'mode={mode} network_name={network_name} ' \
                              'ipaddress={ipv4} ' \
                              'xmit_hash_policy={xmit_hash_policy}'

        network_interface_url = node_path + '/network_interfaces/'

        for slave_eth in slave_nics:
            nic_name = slave_eth['NAME']
            eth_path = network_interface_url + nic_name
            props = eth_props_template.format(
                nic_name, slave_eth['MAC'], self.bond_name,
                self.initial_txqueuelen_value)

            self.execute_cli_create_cmd(self.ms_node, eth_path, 'eth', props)
            self.add_nic_to_cleanup(hostname, nic_name)

        bond_path = network_interface_url + self.bond_name

        props = bond_props_template.format(
            device_name=self.bond_name,
            network_name=self.test_network_name,
            ipv4=address,
            mode=self.bond_mode,
            xmit_hash_policy=self.bond_initial_xmit_policy)

        self.execute_cli_create_cmd(self.ms_node, bond_path, 'bond', props)
        self.add_nic_to_cleanup(hostname, self.bond_name, flush_ip=True)

    def _model_standalone_node_nic(self):
        """
          Model a LITP eth device on a node.
        """
        name = self.n1_nics[0]['NAME']
        eth_props_template = 'device_name={0} macaddress={1} txqueuelen={2} ' \
                             'ipaddress={3} network_name={4}'
        eth_path = self.mn_net_url[0] + '/{0}'.format(name)

        props = eth_props_template.format(
            name, self.n1_nics[0]['MAC'], self.initial_txqueuelen_value,
            self.test_address_n1, self.test_network_name)

        self.execute_cli_create_cmd(self.ms_node, eth_path, 'eth', props)
        self.add_nic_to_cleanup(self.peer_nodes[0], name, flush_ip=True)

    def _assert_xmit_policy_applied(self, expected_xmit_policy):
        """
        Assert the bonds modeled xmit_hash_policy value is set on the
        physical bond interface.

        Args:
            expected_xmit_policy (str): expected_xmit_policy value
        """
        ifcfg_file = '{0}/ifcfg-{1}'.format(
            test_constants.NETWORK_SCRIPTS_DIR, self.bond_name)

        sys_file = '/sys/class/net/{0}/bonding/xmit_hash_policy'.format(
                self.bond_name)

        for host in self.peer_nodes:
            stdout = self.get_file_contents(host, ifcfg_file)
            bond_opts_key = 'BONDING_OPTS="mode={0} xmit_hash_policy={1}' \
                            '"'.format(self.bond_mode, expected_xmit_policy)
            self.assertTrue(self.is_text_in_list(bond_opts_key, stdout),
                            'Bond policy not exposed correctly on {0}'.format(
                                    host))
            stdout = self.get_file_contents(host, sys_file)

            # Check the /sys/class/net file has the changes too
            self.assertTrue(self.is_text_in_list(expected_xmit_policy, stdout),
                            'Bond policy not set correctly on {0}'.format(
                                    host))

    def _assert_txqueuelen(self, expected):
        """
        Asserts modeled txqueuelen value is set on physical eth interfaces.

        Args:
            expected (str): The value that should be set on the physical
                device.
        """
        for slave in self.n1_nics:
            self._assert_txqueuelen_applied(
                self.peer_nodes[0], slave['NAME'], expected)

        for slave in self.n2_nics:
            self._assert_txqueuelen_applied(
                self.peer_nodes[1], slave['NAME'], expected)

    def _assert_txqueuelen_applied(self, host, nic, expected_txq):
        """
        Asserts physical eth device has expected txqueuelen set.

        Args:
            host (str) : The host the eth is on
            nic (str) : The eth name
            expected_txq (str) : The txqueuelen value that is expected to
                be set.
        """
        applied_value = self._get_txqueuelen(host, nic)
        self.assertNotEqual(None, applied_value)
        self.assertEqual(
                expected_txq, applied_value,
                '{0}:Live value {1} is not what is modeled and expected:'
                '{2}'.format(host, applied_value, expected_txq))

    def assert_no_task_plan(self):
        """
        Asserts no tasks created when create_plan is called.
        """
        _, stderr, _ = self.run_command(self.ms_node,
                                        self.cli.get_create_plan_cmd())
        self.assertTrue(self.is_text_in_list(
                        "Create plan failed: no tasks were generated",
                        stderr),
                        "Unexpected plan created")

    def ensure_error_on_txqueuelen_removed(self, node_path, nic):
        """
        Delete the txqueuelen property from the nic.
        Create a plan and assert it fails with a ValidationError.
        Restores the model.

        Args:
              node_path(str) : Model path of the LITP node.
              nic (str) : NIC name
        """
        nic_path = node_path + '/network_interfaces/' + nic
        self.execute_cli_update_cmd(self.ms_node, nic_path,
                                    'txqueuelen', action_del=True)

        _, stderr, _ = self.execute_cli_createplan_cmd(
            self.ms_node, expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError', stderr))
        self.assertTrue(self.is_text_in_list(
            'The txqueuelen property can not be removed once set',
            stderr))

        self.execute_cli_restoremodel_cmd(self.ms_node)

    @attr('all', 'revert', 'story196696', 'story196696_tc01')
    def test_01_p_bonded_nics_txqueuelen_bond_xmit_policy(self):
        """
        @tms_id: torf_196696_tc01
        @tms_requirements_id: TORF-196696
        @tms_title: Create a bond with mode=4 and xmit_hash_policy=layer3+4 and
                    slave nics with txqueuelen set.
        @tms_description: With an already up and running LITP environment,
                          create a bond with 2 slave eth devices. The bonds
                          mode is 4 and its xmit_hash_policy set to layer3+4.
                          Both slave eth devices have txqueuelen set to a non
                          default value. Verify changes are made to the running
                          system. Update the txqueuelen of one of the slave
                          nics and verify changes on the running system.
        @tms_test_steps:
            @step: Create a test network and create bonds with xmit_hash_policy
                   and tx_queue props.
            @result: The LITP items are created.
            @step: Create and Run plan.
            @result: The plan is successful.
            @step: Ensure xmit_hash_policy and txqueuelen configuration are
                   applied.
            @result: xmit_hash_policy and txqueuelen configuration are as
                     expected.
            @step: Create plan and ensure no tasks were generated.
            @result: No plan is created and a DoNothingPlanError can be
                     seen.
            @step: Update the txqueuelen and xmit_hash_policy properties on the
                   peer nodes.
            @result: The LITP items are updated.
            @step: Create and Run plan.
            @result: Plan is in Running State.
            @step: Restart LITP after the eth configuration has been applied
                   to the specified node.
            @result: LITP restarts successfully.
            @step: Recreate the plan and verify the applied configuration
                   is not present into the new plan.
            @result: The configuration is as expected.
            @step: Rerun the plan and wait for it to complete.
            @result: The plan is successful.
            @step: Ensure xmit_hash_policy and txqueuelen configuration are
                   applied.
            @result: xmit_hash_policy and txqueuelen configuration are as
                     expected.
            @step: Create a plan and ensure no tasks were generated.
            @result: No plan is created and a DoNothingPlanError can be
                     seen.
            @step: Update the tx_ring_buffer of the first slave nic on node1
                   and the second slave nic on node2.
            @result: The LITP items are updated.
            @step: Create and Run plan.
            @result: The plan is successful.
            @step: Ensure the txqueuelen value have not changed.
            @result: txqueuelen is as expected.
            @step: Create a plan and ensure no tasks were generated.
            @result: No plan is created and a DoNothingPlanError can be
                         seen.
            @step: Delete the txqueuelen property on node1.
            @result: Property is deleted.
            @step: Create a plan and assert it fails with a ValidationError.
            @result: A ValidationError is raised stating the property can't
                     be deleted once it has been set.
            @step: Restore model.
            @result: Model is restored, and deleted property is back in model.
            @step: Create a plan and ensure no tasks were generated.
            @result: No plan is created and a DoNothingPlanError can be
                     seen.
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.assertEqual(2, len(self.n1_nics),
                         'Could not get the 2 required eth devices on node1')
        self.assertEqual(2, len(self.n2_nics),
                         'Could not get the 2 required eth devices on node2')

        self.log('info', '# 1. Create a test network and create bonds with'
                         ' xmit_hash_policy and tx_queue props.')
        self.execute_cli_create_cmd(
            self.ms_node, self.test_network_url, 'network',
            'name={0} subnet={1}'.format(self.test_network_name,
                                         self.test_network_cidr))

        self._model_bond(self.node_urls[0], self.n1_nics, self.test_address_n1,
                         self.peer_nodes[0])

        self._model_bond(self.node_urls[1], self.n2_nics, self.test_address_n2,
                         self.peer_nodes[1])

        self.log('info', '# 2.Create and Run plan.')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE,
                                plan_timeout_mins=5)

        self.log('info', '# 3.Ensure xmit_hash_policy and txqueuelen '
                         'configuration are applied.')
        self._assert_xmit_policy_applied(self.bond_initial_xmit_policy)
        self._assert_txqueuelen(self.initial_txqueuelen_value)

        self.log('info', '# 4.Create plan and ensure no tasks were generated.')
        self.assert_no_task_plan()

        self.log('info', '# 5.Update the txqueuelen and xmit_hash_policy'
                         ' properties on the peer nodes.')

        nics = {self.mn_net_url[0]: self.n1_nics,
                self.mn_net_url[1]: self.n2_nics}

        for net_url, nics in nics.iteritems():
            for nic in nics:
                nic_path = net_url + '/{0}'.format(nic['NAME'])
                self.execute_cli_update_cmd(
                    self.ms_node, nic_path,
                    'txqueuelen=' + self.updated_txqueuelen_value)

                nic_path = net_url + '/{0}'.format(self.bond_name)
                self.execute_cli_update_cmd(
                    self.ms_node, nic_path,
                    'xmit_hash_policy=' + self.bond_updated_xmit_policy)

        self.log('info', '# 6.Create and Run plan.')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        wait_for_phase_success = 'Update eth "{0}" on node "{1}"'. \
            format(self.n1_nics[1]['NAME'], self.peer_nodes[0])
        self.log('info', '# 7. Restart LITP after the eth configuration has'
                         ' been applied to {0} : {1}.'.format(
                            self.peer_nodes[0], wait_for_phase_success))
        self.restart_litpd_when_task_state(
            self.ms_node, wait_for_phase_success, timeout_mins=10,
            task_state=test_constants.PLAN_TASKS_SUCCESS)

        self.log('info', '# 8. Recreate the plan and verify the applied '
                         'configuration is not present in the new plan.')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.assertEqual(test_constants.CMD_ERROR,
                         self.get_task_state(self.ms_node,
                                             wait_for_phase_success,
                                             False))

        self.log('info', '# 9.Rerun the plan and wait for it to complete.')
        self.execute_cli_runplan_cmd(self.ms_node)
        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 test_constants.
                                                 PLAN_COMPLETE,
                                                 timeout_mins=5),
                        'The plan execution did not succeed')

        self.log('info', '# 10.Ensure the txqueuelen and xmit_hash_policy '
                         'configuration is applied.')
        self._assert_txqueuelen(self.updated_txqueuelen_value)
        self._assert_xmit_policy_applied(self.bond_updated_xmit_policy)

        self.log('info', '# 11.Create a plan and ensure no tasks were '
                         'generated.')
        self.assert_no_task_plan()

        self.log('info', '# 12.Update the tx_ring_buffer of the first slave'
                         ' eth device on node1 and the second slave'
                         ' eth device on node2')

        nic_path = self.mn_net_url[0] + '/{0}'.format(self.n1_nics[0]['NAME'])
        self.execute_cli_update_cmd(
            self.ms_node, nic_path, 'tx_ring_buffer=512')

        nic_path = self.mn_net_url[1] + '/{0}'.format(self.n2_nics[1]['NAME'])
        self.execute_cli_update_cmd(
            self.ms_node, nic_path, 'tx_ring_buffer=512')

        self.log('info', '# 13.Create and Run plan.')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE,
                                plan_timeout_mins=5)

        self.log('info', '# 14.Ensure the txqueuelen value has not changed.')
        self._assert_txqueuelen(self.updated_txqueuelen_value)

        self.log('info', '# 15.Create a plan and ensure no tasks were '
                         'generated.')
        self.assert_no_task_plan()

        self.log('info', '# 16.Delete the txqueuelen property on node1. '
                         'Create a plan and assert it fails with a '
                         'ValidationError. Restore model.')
        self.ensure_error_on_txqueuelen_removed(self.node_urls[0],
                                                self.n1_nics[0]['NAME'])

        self.log('info', '# 17.Create a plan and ensure no tasks '
                         'were generated.')
        self.assert_no_task_plan()

    @attr('all', 'revert', 'story196696', 'story196696_tc02')
    def test_02_p_unbonded_nic_txqueuelen(self):
        """
            @tms_id: torf_196696_tc02
            @tms_requirements_id: TORF-196696
            @tms_title: Update the txqueulen value of an eth item that's not
                        part of a bond
            @tms_description: With an already up and running LITP environment,
                              create 1 eth item with no master set and with
                              txqueuelen set to some non default value.
                              Verify changes are made to the running system.
                              Then, update the txqueuelen property for that NIC
                              and verify changes on the running system.
            @tms_test_steps:
                @step: Create test network and an eth interface with
                       txqueuelen.
                @result: The LITP items are created.
                @step: Create and Run plan.
                @result: The plan is successful.
                @step: Ensure the txqueuelen configuration is applied.
                @result: txqueuelen configuration is as expected.
                @step: Create a plan and ensure no tasks were generated.
                @result: No plan is created and a DoNothingPlanError can be
                         seen.
                @step: Delete the txqueuelen property from the nic
                @result: Property is deleted.
                @step: Create a plan and assert it fails with a VaidationError.
                @result: A ValidationError is raised stating the property can't
                         be deleted once it has been set.
                @step: Restore model.
                @result: Model is restored, and deleted property is back in
                         model.
                @step: Create a plan and ensure no tasks were generated.
                @result: No plan is created and a DoNothingPlanError can be
                         seen.
                @step: Update the txqueuelen property of nic.
                @result: The LITP item is updated.
                @step: Create and Run plan.
                @result: The plan is successful.
                @step: Ensure the txqueuelen configuration is applied.
                @result: txqueuelen configuration is as expected.
                @step: Create a plan and ensure no tasks were generated.
                @result: No plan is created and a DoNothingPlanError can be
                         seen.
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', '# 1. Create test network and an eth interface with '
                         'txqueuelen.')
        self.execute_cli_create_cmd(
            self.ms_node, self.test_network_url,
            'network', 'name={0} subnet={1}'.format(self.test_network_name,
                                                    self.test_network_cidr))

        self._model_standalone_node_nic()

        self.log('info', '# 2.Create and Run plan.')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE,
                                plan_timeout_mins=5)

        self.log('info', '# 3.Ensure the txqueuelen configuration is applied.')
        test_nic = self.n1_nics[0]['NAME']
        self._assert_txqueuelen_applied(
            self.peer_nodes[0], test_nic, self.initial_txqueuelen_value)

        self.log('info', '# 4.Create a plan and ensure no tasks were '
                         'generated.')
        self.assert_no_task_plan()

        self.log('info', '# 5.Delete the txqueuelen property from the nic. '
                         'Create a plan and assert it fails with a '
                         'ValidationError. Restore model.')
        self.ensure_error_on_txqueuelen_removed(self.node_urls[0], test_nic)

        self.log('info', '# 6.Create a plan and ensure no tasks were '
                         'generated.')
        self.assert_no_task_plan()

        self.log('info', '# 7.Update the txqueuelen property of nic')
        nic_path = self.mn_net_url[0] + '/{0}'.format(test_nic)
        self.execute_cli_update_cmd(
            self.ms_node, nic_path,
            'txqueuelen={0}'.format(self.updated_txqueuelen_value))

        self.log('info', '# 8.Create and Run plan.')
        self.run_and_check_plan(self.ms_node, test_constants.PLAN_COMPLETE,
                                plan_timeout_mins=5)

        self.log('info', '# 9.Ensure the txqueuelen configuration is '
                         'applied.')
        self._assert_txqueuelen_applied(
            self.peer_nodes[0], test_nic, self.updated_txqueuelen_value)

        self.log('info', '# 10.Create a plan and ensure no tasks '
                         'were generated.')
        self.assert_no_task_plan()
