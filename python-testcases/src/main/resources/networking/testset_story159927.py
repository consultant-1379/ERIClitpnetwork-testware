"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     January 2017
@author:    Ciaran Reilly
@summary:   Integration
            Agile: STORY-159927
"""

from litp_generic_test import GenericTest, attr
import test_constants as const


class Story159927(GenericTest):
    """
    TORF-159927: As a LITP user i want to be able to modify subnet definition
    in the model and have the networking plugin act accordingly
    """

    def setUp(self):
        """
        Runs before every single test
        """
        super(Story159927, self).setUp()

        self.ms_node = self.get_management_node_filename()
        self.primary_node = self.get_managed_node_filenames()[0]

        self.vcs_cluster_url = self.find(self.ms_node,
                                         '/deployments', 'vcs-cluster')[-1]

        self.ms_url = "/ms"
        self.primary_node_url = self.get_node_url_from_filename(
            self.ms_node, self.primary_node)

        self.ms_net_url = self.find(self.ms_node, self.ms_url,
                                    'collection-of-network-interface')[0]
        self.primary_node_net_url = self.find(self.ms_node,
                                       self.primary_node_url,
                                       'collection-of-network-interface')[0]

        self.nodes_urls = self.find(self.ms_node, self.vcs_cluster_url,
                                    'node')
        self.node_ids = [node.split('/')[-1] for node in self.nodes_urls]

        self.nodes_to_expand = []

        self.node_exe = [self.get_node_filename_from_url(self.ms_node, node)
                         for node in self.nodes_urls]

        self.networks_url = self.find(self.ms_node,
                                      '/infrastructure',
                                      'collection-of-network')[-1]

        self.vcs_network_hosts_url = self.find(self.ms_node,
                                     self.vcs_cluster_url,
                                    'collection-of-vcs-network-host')[0]

        self.management_network = self.get_management_network_name(
                                  self.ms_node)

    def tearDown(self):
        """
        Runs after every single test
        """
        super(Story159927, self).tearDown()

        self.execute_cli_update_cmd(self.ms_node,
                                    "{0}/mgmt".format(self.networks_url),
                                    props='subnet=192.168.0.0/24')

    def _create_bonds_and_bridges(self, props):
        """
        Method that creates the bonds and bridges for relevant test cases

        Args:
            props (dict): Holds network properties that will be created
        """

        self.log('info', 'Backup all networking files and find free interface '
                         'on MNs and MS in cluster')
        test_ms_if1 = \
            self.verify_backup_free_nics(self.ms_node, "/ms",
                                         backup_files=True)[0]

        self.log('info', 'Create new network ({0})'.format(props['name']))

        network_url = '{0}/{1}'.format(self.networks_url, props['name'])
        network_props = "name='{0}' subnet='{1}'".format(props['name'],
                                                         props['subnet'])

        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", network_props,
                                    add_to_cleanup=True)

        self.log('info', 'Create new interfaces and bonds on MS and '
                 'MNs using new network ({0})'.format(props['name']))

        eth_url_ms = '{0}/{1}'.format(self.ms_net_url,
                                     test_ms_if1['NAME'])
        eth_props_ms = "device_name='{0}' macaddress='{1}' master='{2}'"\
            .format(test_ms_if1['NAME'], test_ms_if1['MAC'], props['bond'])

        bridge_url_ms = '{0}/{1}'.format(self.ms_net_url,
                                         props['br_dev'])
        bridge_props_ms = "ipaddress='{0}' device_name='{1}' " \
                          "ipv6address='fe05::1' network_name='{2}'"\
            .format(props['ipaddresses'][0], props['br_dev'],
                    props['name'])

        bond_url_ms = '{0}/{1}'.format(self.ms_net_url,
                                       props['bond'])
        bond_props_ms = "device_name='{0}' bridge='{1}' miimon='100'"\
            .format(props['bond'], props['br_dev'])

        self.execute_cli_create_cmd(self.ms_node, eth_url_ms, "eth",
                                    eth_props_ms, add_to_cleanup=True)
        self.execute_cli_create_cmd(self.ms_node, bridge_url_ms,
                                    "bridge",
                                    bridge_props_ms, add_to_cleanup=True)
        self.execute_cli_create_cmd(self.ms_node, bond_url_ms,
                                    "bond",
                                    bond_props_ms, add_to_cleanup=True)

        # Cleaning up bridge eth and bond after test case finishes

        self.add_nic_to_cleanup(self.ms_node,
                                '{0}'.format(test_ms_if1['NAME']),
                                flush_ip=True)
        self.add_nic_to_cleanup(self.ms_node, 'br2', is_bridge=True,
                                flush_ip=True)
        self.add_nic_to_cleanup(self.ms_node, 'bond_2', is_bond=True)

        # Node Network assignment
        for node, i, node_exe in zip(self.nodes_urls,
                                     xrange(1, len(self.nodes_urls) + 1),
                                     self.node_exe):
            free_nics = \
                self.verify_backup_free_nics(self.ms_node, node,
                                             backup_files=True)
            test_if1 = free_nics[0]

            eth_url_node = '{0}/network_interfaces/{1}'.format(node,
                            test_if1['NAME'])

            eth_props_node = "device_name='{0}' macaddress='{1}' " \
                             "master='{2}'".format(test_if1["NAME"],
                                                   test_if1["MAC"],
                                                   props['bond'])

            br_url_n1 = '{0}/network_interfaces/{1}'.format(node,
                            props['br_dev'])

            bridge_props_n1 = "ipaddress='{0}' device_name='{1}' " \
                              "network_name='{2}'"\
                .format(props['ipaddresses'][i], props['br_dev'],
                        props['name'])

            bond_url_node = '{0}/network_interfaces/{1}'.format(node,
                            props['bond'])
            bond_props_node = "device_name='{0}' bridge='{1}' miimon='100'"\
                .format(props['bond'], props['br_dev'])

            self.execute_cli_create_cmd(self.ms_node, eth_url_node,
                                        "eth", eth_props_node,
                                        add_to_cleanup=True)
            self.execute_cli_create_cmd(self.ms_node, br_url_n1,
                                        "bridge", bridge_props_n1,
                                        add_to_cleanup=True)
            self.execute_cli_create_cmd(self.ms_node, bond_url_node,
                                        "bond", bond_props_node,
                                        add_to_cleanup=True)
            # Cleaning up bridge eth and bond after test case finishes

            self.add_nic_to_cleanup(node_exe, '{0}'
                                    .format(test_if1['NAME']),
                                    flush_ip=True)
            self.add_nic_to_cleanup(node_exe, 'br2', is_bridge=True,
                                    flush_ip=True)
            self.add_nic_to_cleanup(node_exe, 'bond_2', is_bond=True,
                                    flush_ip=True)

    def _create_bonds_and_bridges_on_primary_node(self, props):
        """
        Description:
            Method that creates the bonds and bridges for the MS and primary
            node.
        Args:
            props (dict) : Properties of the network to be created.
        """

        self.log('info', 'Backup all networking files and find free interface '
                         'on MNs and MS in cluster')
        test_ms_if1 = self.verify_backup_free_nics(
            self.ms_node, self.ms_url, backup_files=True)[0]

        # Create new network for mgmt_2
        network_url = self.networks_url + '/{0}'.format(props['name'])
        network_props = "name='{0}' subnet='{1}'".format(props['name'],
                                                         props['subnet'])
        self.execute_cli_create_cmd(self.ms_node, network_url,
                                    "network", network_props)

        # Instantiate the network on the MS
        eth_url_ms = self.ms_net_url + "/{0}".format(test_ms_if1['NAME'])
        eth_props_ms = "device_name='{0}' macaddress='{1}' master='{2}'"\
            .format(test_ms_if1['NAME'], test_ms_if1['MAC'], props['bond'])

        bridge_url_ms = self.ms_net_url + "/{0}".format(props['br_dev'])
        bridge_props_ms = "ipaddress='{0}' device_name='{1}' " \
                          "ipv6address='fe05::1' network_name='{2}'" \
            .format(props['ipaddresses'][0], props['br_dev'],
                    props['name'])

        bond_url_ms = self.ms_net_url + "/{0}".format(props['bond'])
        bond_props_ms = "device_name='{0}' bridge='{1}' miimon='100'".format(
            props['bond'], props['br_dev'])

        self.execute_cli_create_cmd(self.ms_node, eth_url_ms, "eth",
                                    eth_props_ms)
        self.execute_cli_create_cmd(self.ms_node, bridge_url_ms,
                                    "bridge",
                                    bridge_props_ms)
        self.execute_cli_create_cmd(self.ms_node, bond_url_ms,
                                    "bond",
                                    bond_props_ms)
        # Cleaning up bridge eth and bond after test case finishes
        self.add_nic_to_cleanup(self.ms_node,
                                test_ms_if1['NAME'],
                                flush_ip=True)
        self.add_nic_to_cleanup(self.ms_node, 'br2',
                                is_bridge=True,
                                flush_ip=True)
        self.add_nic_to_cleanup(self.ms_node, 'bond_2',
                                is_bond=True)

        # Node Network assignment
        test_if1 = self.verify_backup_free_nics(self.ms_node,
                                                self.primary_node_url)[0]

        eth_url_node = self.primary_node_net_url + "/{0}".format(
            test_if1['NAME'])
        eth_props_node = "device_name='{0}' macaddress='{1}' " \
                         "master='{2}'".format(test_if1["NAME"],
                                               test_if1["MAC"],
                                               props['bond'])

        br_url_n1 = self.primary_node_net_url + "/{0}".format(props['br_dev'])
        bridge_props_n1 = "ipaddress='{0}' device_name='{1}' " \
                          "network_name='{2}'" \
            .format(props['ipaddresses'][1], props['br_dev'],
                    props['name'])

        bond_url_node = self.primary_node_net_url + "/{0}".format(
            props['bond'])
        bond_props_node = "device_name='{0}' bridge='{1}' miimon='100'" \
            .format(props['bond'], props['br_dev'])

        self.execute_cli_create_cmd(self.ms_node, eth_url_node,
                                    "eth", eth_props_node)
        self.execute_cli_create_cmd(self.ms_node, br_url_n1,
                                    "bridge", bridge_props_n1)
        self.execute_cli_create_cmd(self.ms_node, bond_url_node,
                                    "bond", bond_props_node)

        # Cleaning up bridge eth and bond after test case finishes
        self.add_nic_to_cleanup(self.primary_node, test_if1['NAME'],
                                flush_ip=True)
        self.add_nic_to_cleanup(self.primary_node, 'br2', is_bridge=True,
                                flush_ip=True)
        self.add_nic_to_cleanup(self.primary_node, 'bond_2', is_bond=True,
                                flush_ip=True)

    def _create_vlans_and_bridges(self, props):
        """
        Method that creates the vlans and bridges for relevant test cases

        Args:
            props (dict): Dictionary of the properties required to create
            the vlans and bridges
        """
        test_ms_if1 = \
            self.verify_backup_free_nics(self.ms_node, "/ms",
                                         backup_files=True)[0]

        # Create new network for mgmt_2

        network_url = '{0}/{1}'.format(self.networks_url, props['name'])
        network_props = "name='{0}' subnet='{1}'".format(props['name'],
                                                         props['subnet'])
        self.execute_cli_create_cmd(self.ms_node, network_url, "network",
                                    network_props)

        # Instantiate the network on the MS

        eth_url_ms = '{0}/{1}'.format(self.ms_net_url,
                     test_ms_if1['NAME'])
        eth_props_ms = "device_name='{0}' macaddress='{1}'"\
            .format(test_ms_if1['NAME'], test_ms_if1['MAC'])

        bridge_url_ms = '{0}/{1}'.format(self.ms_net_url,
                        props['br_dev'])
        bridge_props_ms = "ipaddress='{0}' device_name='{1}' " \
                          "ipv6address='fe05::1' network_name='{2}'"\
            .format(props['ipaddresses'][0], props['br_dev'],
                    props['name'])

        vlan_url_ms = '{0}/{1}'.format(self.ms_net_url,
                      props['vlan_name'])
        vlan_props_ms = "device_name='{0}' bridge='{1}'".format((
            props['dev_name'].format(test_ms_if1['NAME'])), props['br_dev'])

        self.execute_cli_create_cmd(self.ms_node, eth_url_ms, "eth",
                                    eth_props_ms,
                                    add_to_cleanup=True)
        self.execute_cli_create_cmd(self.ms_node, bridge_url_ms,
                                    "bridge", bridge_props_ms,
                                    add_to_cleanup=True)
        self.execute_cli_create_cmd(self.ms_node, vlan_url_ms,
                                    "vlan", vlan_props_ms,
                                    add_to_cleanup=True)

        # Cleaning up bridge eth and vlan after test case finishes
        self.add_nic_to_cleanup(self.ms_node,
                                '{0}'.format(props['br_dev']), is_bridge=True,
                                flush_ip=True)
        self.add_nic_to_cleanup(self.ms_node,
                                '{0}'.format(test_ms_if1['NAME']),
                                flush_ip=True)
        self.add_nic_to_cleanup(self.ms_node, '{0}'.format(
            props['dev_name'].format(test_ms_if1['NAME'])), flush_ip=True)

        for node, i, node_exe in zip(self.nodes_urls,
                           xrange(1, len(self.nodes_urls) + 1),
                           self.node_exe):
            free_nics = \
                self.verify_backup_free_nics(self.ms_node, node,
                                             backup_files=True)
            test_if1 = free_nics[0]

            eth_url_node = '{0}/network_interfaces/{1}'.format(node,
                           test_if1['NAME'])

            eth_props_node = "device_name='{0}' macaddress='{1}'"\
                .format(test_if1["NAME"], test_if1["MAC"])

            br_url_n1 = '{0}/network_interfaces/{1}'.format(node,
                          props['br_dev'])
            bridge_props_n1 = "ipaddress='{0}' device_name='{1}' " \
                              "network_name='{2}'"\
                .format(props['ipaddresses'][i], props['br_dev'],
                        props['name'])

            vlan_url_node = '{0}/network_interfaces/{1}'.format(node,
                            props['vlan_name'])
            vlan_props_node = "device_name='{0}' bridge='{1}'"\
                .format((props['dev_name'].format(test_if1['NAME'])),
                        props['br_dev'])

            self.execute_cli_create_cmd(self.ms_node, eth_url_node,
                                        "eth", eth_props_node,
                                        add_to_cleanup=True)
            self.execute_cli_create_cmd(self.ms_node, br_url_n1,
                                        "bridge", bridge_props_n1,
                                        add_to_cleanup=True)
            self.execute_cli_create_cmd(self.ms_node, vlan_url_node,
                                        "vlan", vlan_props_node,
                                        add_to_cleanup=True)

            # Cleaning up bridge eth and vlan after test case finishes
            self.add_nic_to_cleanup(node_exe, '{0}'.format(props['br_dev']),
                                    is_bridge=True,
                                    flush_ip=True)
            self.add_nic_to_cleanup(node_exe, '{0}'.format(test_if1['NAME']),
                                    flush_ip=True)
            self.add_nic_to_cleanup(node_exe, '{0}'
                                    .format(props['dev_name']
                                            .format(test_if1['NAME'])),
                                    flush_ip=True)

    def _update_relevant_net_properties(self, net_props):

        """
        Method to update any relevent network properties needed after updating
        the network subnet

        Args:
            net_props (list): List of updated IP addresses
        """

        self.execute_cli_update_cmd(self.ms_node, '{0}/br2'.format(
                                    self.ms_net_url),
                                    props='ipaddress={0}'
                                    .format(net_props[-1]))

        for model_addrs, ip_addrs in zip(self.nodes_urls, net_props):

            node_url = '{0}/br2'.format(self.find(self.ms_node, model_addrs,
                          'collection-of-network-interface')[0])

            self.execute_cli_update_cmd(self.ms_node, node_url,
                                        props='ipaddress={0}'.format(ip_addrs))

    def set_Passwords(self):
        """
        Method that sets the passwords for newly expanded nodes
        """
        for node in self.nodes_to_expand:
            self.assertTrue(self.set_pws_new_node(self.ms_node,
                                                  node),
                            "Failed to set password for "
                            "node '{0}'".format(node))

            stdout, _, _ = self.run_command(node, 'hostname')

            self.assertEqual(stdout[0], node)

    def _add_new_cluster(self):
        """
        Description:
            This Method performs an initial deployment of a VCS Cluster

        Steps:
            1. Create New VCS Cluster
            2. Expand cluster with new node
            3. Create two new cluster service in c2 with initial/ dependency
            list present
        """
        vcs_cluster_url = '{0}/c2'.format(self.find(self.ms_node,
                          '/deployments', 'cluster', False)[0])
        vcs_cluster_props = 'cluster_type=sfha cluster_id=2 ' \
                            'low_prio_net=mgmt llt_nets=hb1,hb2 ' \
                            'cs_initial_online=on app_agent_num_threads=2'
        self.nodes_to_expand.append("node2")

        # Step 1: Create New Cluster 'C2'
        self.execute_cli_create_cmd(self.ms_node, vcs_cluster_url,
                                    'vcs-cluster', vcs_cluster_props,
                                    add_to_cleanup=False)

        # Step 2: Expand new cluster with two new nodes
        self.execute_expand_script(self.ms_node, 'expand_cloud_c2_mn2.sh')

    def _update_sysparam(self, node_url):
        """
        Description:
            Method that adds sysparam items to nodes.
        Args:
            node_url (str) : The path to the node in the model.
        """
        sysparam = self.find(self.ms_node, node_url,
                             'collection-of-sysparam')[0]

        # Need two tasks within the node lock as first one will run
        # to completion when litpd restart is performed later in test
        props = 'key="net.core.wmem_max" value="524287"'
        url = sysparam + '/sysctrl_02'
        self.execute_cli_create_cmd(
            self.ms_node, url, 'sysparam', props)

        props = 'key="net.core.rmem_max" value="524287"'
        url = sysparam + '/sysctrl_03'
        self.execute_cli_create_cmd(
            self.ms_node, url, 'sysparam', props)

    #@attr('pre-reg', 'revert', 'story159927', 'story159927_tc01')
    def obsolete_test_01_p_update_subnet_with_bond_and_bridges(self):
        """
        ###Obsoleted due to functionality is already covered in
        test_10_p_updte_subnet_netwrk_confd_bridged_bonds_mult_eths

        ###tms_id: torf_159927_tc01
        ###tms_requirements_id: TORF-159927
        ###tms_title: Update network subnet configured with bonds and bridges
        ###tms_description:
            Test to verify that a user can update the subnet of a network
            while said network is configured with multiple eths and bridged
            with bonds
        ###tms_test_steps:
            #step: Backup all networking files and find free interface on MNs
            and MS in cluster
            #result: Free interfaces from MS and MNs are stored in dictionary
            #step: Create new network (mgmt_2)
            #result: New Network created in model
            #step: Create new interfaces and bonds on the MS and MNs using the
                   new network
            #result: New items created in model
            #step: Create/ Run Plan
            #result: Plan completes successfully
            #step: Update mgmt network subnet. Expand it to now also include
                   the full range covered by network mgmt_2 created previously
            #result: mgmt subnet is expanded in model
            #step: Update mgmt_2 network subnet. Change it to cover a new range
            #result: mgmt_2 subnet is updated in the model
            #step: Update IP addresses of interfaces on mgmt_2 to have new
                   addresses in the new range
            #result: IP addresses are updated in the model
            #step: Create/run plan
            #result: Plan completes succesfully
            #step: Test mgmt network IPs using ping
            #result: Ping of IPs is successful
            #step: Test mgmt_2 network IPs using ping
            #result: Ping of updated IPs are successful
        ###tms_test_precondition: NA
        ###tms_execution_type: Automated
        """

    @attr('all', 'revert', 'story159927', 'story159927_tc02')
    def test_02_p_update_subnet_with_vlan_and_bridges(self):
        """
        @tms_id: torf_159927_tc02
        @tms_requirements_id: TORF-159927
        @tms_title: Update network subnet configured with vlans and bridges
        @tms_description:
        Test to verify that a user can update the subnet of a network
        configured with vlans and bridges
        @tms_test_steps:
            @step: Reduce the subnet of the mgmt network to allow a second
                   network to be created later in the test
            @result: network updated in the model
            @step: Create/Run plan
            @result: Plan completes successfully
            @step: Backup all networking files and find free interface on MNs
                   and MS in cluster
            @result: Free interfaces from MS and MNs are stored in dictionary
            @step: Create new network (mgmt_2)
            @result: New network created in model
            @step: Create new interfaces and vlans on MS and MNs using new
                   network
            @result: New items created in model
            @step: Create/Run Plan
            @result: Plan completes successfully
            @step: Update mgmt network subnet. Expand it to now also include
                   the full range covered by network mgmt_2 created previously
            @result: mgmt subnet is expanded in model
            @step: Update IP addresses of interfaces with bridges and vlans on
                   mgmt_2 to have new addresses in new range.
            @result: IP addresses are updated in the model
            @step: Create/Run Plan
            @result: Plan completes successfully
            @step: Test mgmt network IPs with ping
            @result: ping of IPs is successful
            @step: Test mgmt_2 updated IPs with ping
            @result: ping of updated IPs is successful
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log("info", "Step 1: Reduce the subnet of the mgmt network to "
                 "allow a second network to be created later in the test")
        #This needs a seperate plan as defined in the docs "When you are
        #updating the network, it is recommended that you do not perform
        #any of the following operations within the same plan:
        #Add new network interfaces
        #Update more than two network subnets

        self.execute_cli_update_cmd(self.ms_node,
                                    "{0}/mgmt".format(self.networks_url),
                                    props='subnet=192.168.0.0/25')

        self.log("info", "Step 2: Create/Run Plan")

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=40)

        mgmt_2_props = {'name': 'mgmt_2', 'subnet': '192.168.1.0/24',
                        'ipaddresses': ['192.168.1.2',
                                        '192.168.1.3',
                                        '192.168.1.4',
                                        '192.168.1.5',
                                        '192.168.1.6'],
                        'vlan_name': 'vlan_2',
                        'br_dev': 'br2', 'dev_name': '{0}.1'}

        self.log('info', 'Step 3: Backup all networking files and find free '
                         'interface on MNs and MS in cluster')
        self._create_vlans_and_bridges(mgmt_2_props)

        self.log('info', 'Step 4: Create/ Run Plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=40)

        self.log('info', 'Step 5: Update all relevant items in model')
        self.execute_cli_update_cmd(self.ms_node,
                                    '{0}/mgmt'.format(self.networks_url),
                                    props='subnet=192.168.0.0/23')

        self.log('info', 'Step 6: Create/ Run plan again performing '
                         'robustness testing')
        self.execute_cli_update_cmd(self.ms_node,
                                    '{0}/{1}'.format(self.networks_url,
                                                     mgmt_2_props['name']),
                                    props='subnet=192.168.2.0/24')

        updated_ipaddresses = ['192.168.2.2', '192.168.2.3', '192.168.2.4',
                               '192.168.2.5', '192.168.2.6']

        self._update_relevant_net_properties(updated_ipaddresses)

        self.log('info', 'Step 7: Create/ Run Plan')

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=40)

        self.log('info', 'Step 8: Ensure network connectivity is restored to '
                         'nodes and MS after plan finishes')
        for node in self.node_exe:
            ping_cmd = self.net.get_ping_cmd(node)
            self.run_command(self.ms_node, ping_cmd, default_asserts=True)

        self.log('info', 'Step 9: Pinging updated IP addresses on new network')
        ping_cmd = self.net.get_ping_cmd(updated_ipaddresses[4])
        self.run_command(self.ms_node, ping_cmd, default_asserts=True)

    @attr('manual-test', 'story159927', 'story159927_tc03')
    def test_03_p_update_subnets_during_idempotent(self):
        """
        @tms_id: torf_159927_tc03
        @tms_requirements_id: TORF-159927
        @tms_title: Update network subnet during idempotency
        @tms_description:
            Test to verify that a user can update the subnet of a network
            during multiple litpd restarts throughout the update
            (robustness test)
        @tms_test_steps:
            @step: Backup all networking files and find free interface on MNs
            and MS in cluster
            @result: Free interfaces from MS and MNs are stored in dictionary
            @step: Create new network with interfaces and bonds on MS and MNs
            using IP address range of litp_management network
            @result: New Network with interfaces and bonds between MS and nodes
            are created
            @step: Create/ Run Plan
            @result: Plan is created and ran
            @step: Update litp_management network to allocate more IPs from
            newly created network in previous plan
            @result: litp_management network is updated to allocate more IPs
            from newly created network
            @step: Update relevant interfaces with bridges and bonds to allow
            new IP range to be allocated to relevent network
            @result: Relevent network interfaces and bridges are updated
            @step: Create/ Run plan
            @result: Plan is created and run
            @step: During update of ifcfg files in litp plan run litpd restart
            @result: litp daemon is restarted
            @step: Create/ Run plan again
            @result: Plan is run to completion
            @step: Ensure network connectivity is restored after plan completes
            and model and nodes are updated
            @result: Network credentials are updated
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        #This test is not run as part of the KGB as it takes 20 minutes to run
        #and the functionality is largely covered by
        #test_10_p_updte_subnet_netwrk_confd_bridged_bonds_mult_eths
        mgmt_2_props = {'name': 'mgmt_2', 'subnet': '192.168.1.0/24',
                        'ipaddresses': ['192.168.1.2',
                                        '192.168.1.3',
                                        '192.168.1.4',
                                        '192.168.1.5',
                                        '192.168.1.6'],
                        'br_dev': 'br2', 'bond': 'bond_2'}

        self.log('info', 'Step 1: Backup all networking files and find free '
                         'interface on MNs and MS in cluster')
        self._create_bonds_and_bridges(mgmt_2_props)

        self.log('info', 'Step 2: Create/ Run Plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=40)

        self.log('info', 'Step 3: Update all relevant items in model')
        self.execute_cli_update_cmd(self.ms_node,
                                    self.networks_url + '/mgmt',
                                    props='subnet=192.168.0.0/23')

        self.execute_cli_update_cmd(self.ms_node,
                                    self.networks_url +
                                    '/{0}'.format(mgmt_2_props['name']),
                                    props='subnet=192.168.2.0/24')

        updated_ipaddresses = ['192.168.2.2',
                               '192.168.2.3',
                               '192.168.2.4',
                               '192.168.2.5',
                               '192.168.2.6']

        self._update_relevant_net_properties(updated_ipaddresses)

        self.log('info', 'Step 4: Create/ Run plan again performing '
                         'robustness testing')
        self.execute_cli_createplan_cmd(self.ms_node)
        task_list = self.get_full_list_of_tasks(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)
        self.perform_repeated_apd_runs(self.ms_node,
                                       task_list,
                                       const.PLAN_TASKS_RUNNING)

        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 const.PLAN_COMPLETE,
                                                 timeout_mins=180))
        self.log('info', 'Step 5: Ensure network connectivity is restored to '
                         'nodes and MS after plan finishes')
        for node in self.node_exe:
            ping_cmd = self.net.get_ping_cmd(node)
            _ = self.run_command(self.ms_node, ping_cmd, default_asserts=True)

        self.log('info', 'Pinging updated IP addresses on new network')
        ping_cmd = self.net.get_ping_cmd(updated_ipaddresses[4])
        _ = self.run_command(self.ms_node, ping_cmd, default_asserts=True)

    @attr('manual-test', 'expansion', 'story159927', 'story159227_tc09')
    def test_09_p_update_subnet_of_networks_in_different_clusters(self):
        """
        @tms_id: torf_159927_tc09
        @tms_requirements_id: TORF-159927
        @tms_title: Update network subnet that exists between two clusters
        @tms_description:
            Test to verify that a user can update the subnet of a network
            while said network is configured on a separate cluster but on
            the same subnet
        @tms_test_steps:
            @step: Create 2 clusters in the litp model along with 2 networks
            that are in the same IP address range
            @result: 2 clusters and 2 networks are created in the LITP model
            @step: Create/ Run Plan
            @result: Plan is created and ran
            @step: Update litp_management network to allocate more IPs from
            network in seperate cluster
            @result: Network is updated with IP address range from other
            cluster
            @step: Update relevant interfaces with bridges and bonds to allow
            new IP range to be allocated to relevent network
            @result: Relevent network interfaces and bridges are updated
            @step: Create/ Run plan
            @result: Plan is created and run
            @step: Ensure network connectivity is restored after plan completes
            and model and nodes are updated
            @result: Network credentials are updated
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        :return:
        """

        self.node_exe = []
        mgmt_2_props = {'name': 'mgmt_2', 'subnet': '192.168.1.0/24',
                        'ipaddresses': ['192.168.1.2',
                                        '192.168.1.3',
                                        '192.168.1.4',
                                        '192.168.1.5'],
                        'br_dev': 'br2', 'bond': 'bond_2'}

        self.log('info', 'Step 1: Add new cluster in litp model')
        self._add_new_cluster()

        self.log('info', 'Create Run plan')

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=40)

        # Set passwords of newly added nodes
        self.set_Passwords()

        # VCS cluster 2 URL and node URL
        vcs_cluster2_url = self.find(self.ms_node, '/deployments',
                                     'vcs-cluster')[0]
        self.nodes_urls.append(self.find(self.ms_node, vcs_cluster2_url,
                                         'node')[0])

        self.node_exe = [self.get_node_filename_from_url(self.ms_node, node)
                         for node in self.nodes_urls]

        self.log('info', 'Step 2: Backup all networking files and find free '
                         'interface on MNs and MS in cluster')
        self._create_bonds_and_bridges(mgmt_2_props)

        self.log('info', 'Create/Run plan')

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=40)

        self.nodes_to_expand.append("node2")

        self.log('info', 'Step 3: Update all relevant items in model')
        self.execute_cli_update_cmd(self.ms_node,
                                    '{0}/mgmt'.format(self.networks_url),
                                    props='subnet=192.168.0.0/23')

        self.execute_cli_update_cmd(self.ms_node,
                                    '{0}/{1}'.format(self.networks_url,
                                    mgmt_2_props['name']),
                                    props='subnet=192.168.2.0/24')

        updated_ipaddresses = ['192.168.2.2', '192.168.2.3', '192.168.2.4',
                               '192.168.2.5']

        self._update_relevant_net_properties(updated_ipaddresses)

        self.log('info', 'Step 5: Create/ Run plan again')

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=40)

        self.log('info', 'Step 6: Ensure network connectivity is restored to '
                         'nodes and MS after plan finishes')
        for node in self.node_exe:
            ping_cmd = self.net.get_ping_cmd(node)
            self.run_command(self.ms_node, ping_cmd, default_asserts=True)

        self.log('info', 'Pinging updated IP addresses on new network')
        ping_cmd = self.net.get_ping_cmd(updated_ipaddresses[3])
        self.run_command(self.ms_node, ping_cmd, default_asserts=True)

    @attr('all', 'revert', 'story159927', 'story159927_tc10')
    def test_10_p_updte_subnet_netwrk_confd_bridged_bonds_mult_eths(self):
        """
        @tms_id: torf_159927_tc10
        @tms_requirements_id: TORF-159927
        @tms_title: Update network subnet on 2 node cluster
        @tms_description: Test designed around Regular Networking KGB suite,
                          as there is no Networking expansion KGB. Hence, this
                          test updates the subnet of a network configured with
                          bonds and bridges, in a 2 node cluster deployment.
                          Changes are only made to one node as a result of
                          refactoring.
        @tms_test_steps:
            @step: Backup all networking files and find free interfaces on MS
                   and MNs in cluster.
            @result: Files backed up and free interfaces found on MS and MNs.
            @step: Create new network items with interfaces and bonds on MS and
                   MNs using IP address range of litp_management network.
            @result: Items created in model.
            @step: Create and Run Plan.
            @result: Plan is created and run to completion.
            @step: Update litp_management network to allocate more IPs from
                   newly created network.
            @result: litp_management network is updated.
            @step: Update network interfaces and bridges affected by subnet
                   change on MS and primary node.
            @result: network interfaces and bridges are updated.
            @step: Add sysparam item in the model for idempotent testing.
            @result: Item added to model.
            @step: Create and Run plan. Run litpd restart after bridge update
                   to relevant network.
            @result: Plan runs to successfully to the specified task
                     description. Sysparam tasks do not exist for first node
                     whereas networking updates do meaning networking tasks are
                     idempotent.
            @step: Create and Run plan. Ensure sysparam tasks are not recreated
                   in plan and networking tasks are idempotent.
            @result: Plan is created and run to completion.
            @step: Ensure network connectivity is restored after plan completes
                   and model and nodes are updated.
            @result: Network credentials are updated.
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', '# 1. Create new network with interfaces and bonds '
                         'on MS and MNs using IP address range of '
                         'litp_management network.')

        mgmt_2_props = {'name': 'mgmt_2',
                        'subnet': '192.169.0.0/16',
                        'ipaddresses': ['192.169.0.2',
                                        '192.169.0.3'],
                        'br_dev': 'br2',
                        'bond': 'bond_2'}

        self._create_bonds_and_bridges_on_primary_node(mgmt_2_props)

        self.log('info', '# 2. Create and Run plan')
        self.run_and_check_plan(self.ms_node,
                                const.PLAN_COMPLETE,
                                plan_timeout_mins=20)

        self.log('info', '# 3. Update litp_management network to allocate '
                         'more IPs from newly created network.')

        self.execute_cli_update_cmd(self.ms_node,
                                    self.networks_url + '/mgmt',
                                    props='subnet=192.168.0.0/15')

        self.execute_cli_update_cmd(self.ms_node,
                                    self.networks_url +
                                    '/{0}'.format(mgmt_2_props['name']),
                                    props='subnet=192.170.0.0/16')

        self.log('info', '# 4. Update network interfaces and bridges affected'
                         ' by subnet change on MS and primary node.')
        updated_ipaddresses = ['192.170.0.2',
                               '192.170.0.6']

        self.execute_cli_update_cmd(self.ms_node,
                                    self.ms_net_url + '/br2',
                                    props='ipaddress={0}'
                                    .format(updated_ipaddresses[-1]))
        self.execute_cli_update_cmd(self.ms_node,
                                    self.primary_node_net_url + '/br2',
                                    props='ipaddress={0}'.format(
                                        updated_ipaddresses[0]))

        self.log('info', '# 5. Add sysparam in the model for idempotent '
                         'testing.')
        self._update_sysparam(self.primary_node_url)

        self.log('info', '# 6. Create and Run plan.')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        self.log('info', '# 7. Run litpd restart after bridge update to '
                         'relevant network .')
        task_desc = 'Set system parameter "net.core.wmem_max" to "524287" ' \
                    'on node "node1"'
        self.assertTrue(
            self.wait_for_task_state(self.ms_node, task_desc,
                                     const.PLAN_TASKS_SUCCESS),
            'Idempotent testing failed during ifcfg update')
        self.restart_litpd_service(self.ms_node)

        self.log('info', '# 8. Create and Run plan. Ensure sysparam tasks are '
                         'not recreated in plan and networking tasks are '
                         'idempotent')
        self.execute_cli_createplan_cmd(self.ms_node)
        self.execute_cli_showplan_cmd(self.ms_node)
        self.execute_cli_runplan_cmd(self.ms_node)

        applied_task = 'Update bridge "br0" on node "node1"'
        self.assertEqual(const.PLAN_TASKS_INITIAL,
                         self.get_task_state(self.ms_node,
                                             applied_task,
                                             ignore_variables=False))
        self.assertEqual(const.CMD_ERROR,
                         self.get_task_state(self.ms_node,
                                             task_desc,
                                             ignore_variables=False))

        self.assertTrue(self.wait_for_plan_state(self.ms_node,
                                                 const.PLAN_COMPLETE,
                                                 timeout_mins=20))

        self.log('info', '# 9. Ensure network connectivity is restored after '
                         'plan completes and model and nodes are updated.')
        node_to_ping = self.get_node_filename_from_url(self.ms_node,
                                                       self.primary_node_url)
        ping_cmd = self.net.get_ping_cmd(node_to_ping)
        self.run_command(
            self.ms_node, ping_cmd, default_asserts=True)

        ping_cmd = self.net.get_ping_cmd(updated_ipaddresses[-1])
        self.run_command(
            self.ms_node, ping_cmd, default_asserts=True)
