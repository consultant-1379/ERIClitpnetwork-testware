"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     March 2016; Refactored Feb 2018
@author:    Stefan Ulian; Aisling Stafford
@summary:   Integration
            Agile: STORY-13259
"""

from litp_generic_test import GenericTest, attr
from networking_utils import NetworkingUtils
import network_test_data as network_data
import test_constants as const


class Story13259(GenericTest):
    """
    As a LITP User I want to be able to configure ARP bonding options so that
    I can use ARP monitoring on bond devices.
    """
    test_ms_if1 = None
    test_node1_if1 = None
    test_node2_if1 = None

    def setUp(self):
        """
        Runs before every single test
        """
        super(Story13259, self).setUp()
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.all_nodes = [self.ms_node] + self.peer_nodes
        self.net = NetworkingUtils()
        self.ms_url = "/ms"
        self.ms_network_path = self.find(self.ms_node, self.ms_url,
                                         "collection-of-network-interface")[0]

        self.node_urls = self.find(self.ms_node, "/deployments",
                                   "node")
        self.all_node_urls = self.node_urls + [self.ms_url]

        self.node1_network_path = self.find(
            self.ms_node, self.node_urls[0],
            "collection-of-network-interface")[0]
        self.node2_network_path = self.find(
            self.ms_node, self.node_urls[1],
            "collection-of-network-interface")[0]

        self.cluster_path = self.find(self.ms_node, "/deployments",
                                      "vcs-cluster")[-1]
        self.cluster_network_hosts_path = self.find(self.ms_node,
                                                    self.cluster_path,
                                                    "collection-of-vcs-" \
                                                    "network-host")[0]

        self.networks_path = self.find(self.ms_node, "/infrastructure",
                                       "network", False)[0]

        self.bond_device_name = network_data.BOND_DEVICE_NAME
        self.bond_arp_ip_target_file = network_data.ARP_IP_TARGET_FILE

        self.path_dict = {
            "{0}_network".format(self.ms_node): self.ms_network_path,
            "ms": self.ms_url,
            "cluster:": self.cluster_path,
            "network": self.networks_path,
            "{0}_network".format(self.peer_nodes[0]): self.node1_network_path,
            "{0}_network".format(self.peer_nodes[1]): self.node2_network_path,
            "vcs_network_host": self.cluster_network_hosts_path,
            "node1": self.node_urls[0],
            "node2": self.node_urls[1]}

    def tearDown(self):
        """
        Runs after every single test
        """
        super(Story13259, self).tearDown()

    def identify_free_nics(self, ms_node, node_paths, node_eths, network=''):
        """
        Description:
        Searches for free nics on the passed in node paths and does a backup
        of the ifconfig files. A free nic is then assigned to the corresponding
        node.

        Args:
        ms_node (str): MS hostname
        node_paths (list) : Node url paths for free nics to be searched on
        """

        for node_path in node_paths:
            free_nics = self.verify_backup_free_nics(ms_node, node_path,
                                                     specific_nics=network)

            hostname = self.get_props_from_url(self.ms_node, node_path,
                                               filter_prop="hostname")
            for node in node_eths:
                if hostname == node["NODE"]:
                    node["PROPS"]["macaddress"] = free_nics[0]["MAC"]
                    node["PROPS"]["device_name"] = free_nics[0]["NAME"]

    def create_update_network_item(self, ms_node, item_dict, update=False,
                                   action_del=False):
        """
        Description:
        Creates/updates a network item based on the passed parameters.

        Args:
        ms_node (str): MS node name
        item_dict (dict) : Dictionary of various properties of
                           the network item to be created/updated

        Kwargs:
        update (bool): Set to True if you want to update an existing item
                       in the given dictionary, False if you want to
                       create the item. Default is False.
        action_del (bool): Set to True if you want to delete the item
                           properties on the specified network.
                           Default is False.
        """

        parent = self.path_dict[item_dict["ITEM_PARENT"]]

        item_type = item_dict["TYPE"]

        item_path = '{0}/{1}'.format(parent, item_dict["NAME"])

        props = ""
        for prop_name, prop_value in item_dict["PROPS"].iteritems():
            if action_del:
                # If update is not True the create command below will raise
                # an exception
                update = True
                props += '{0} '.format(prop_value)
            else:
                props += '{0}="{1}" '.format(prop_name, prop_value)

        if update:
            self.execute_cli_update_cmd(ms_node, item_path, props,
                                        action_del=action_del)
        else:
            self.execute_cli_create_cmd(ms_node, item_path, item_type,
                                        props)

    def reg_cleanup_bond(self):
        """
        Description:
        Register the nodes for cleanup of bonds
        """
        for node in self.all_nodes:
            self.add_nic_to_cleanup(node, self.bond_device_name, is_bond=True)

    def check_bond_file(self, path=const.BOND_FILES_DIR):
        """
        Description:
        Verifies the correct bond properties have been applied

        Kwargs:
        path (str): Unless path to bond file is specified, default path used
                    in this method is to the bonds directory
        """

        if path == self.bond_arp_ip_target_file:
            bond_props = network_data.BOND_ARP_MS["PROPS"]
            bond_params = self.get_file_contents(self.ms_node, path)

            self.assertFalse(' '.join(
                bond_props['arp_ip_target']) in bond_params)
        else:

            for node in self.all_nodes:
                network_path = self.path_dict["{0}_network".format(node)]
                bond_props = self.get_props_from_url(
                    self.ms_node, '{0}/{1}'.format(network_path,
                                                   network_data.BOND_NAME))
                bond_params = self.get_file_contents(node, "{0}/{1}".format(
                    path, self.bond_device_name))

                error_msg = 'The expected string {0} not found'
                if "arp_ip_target" in bond_props:
                    expected_string = 'ARP Polling Interval (ms): {0}'. \
                                    format(bond_props['arp_interval'])
                    self.assertTrue(expected_string in bond_params,
                                    error_msg.format(expected_string))
                    expected_string = 'ARP IP target/s (n.n.n.n form): {0}'\
                        .format(bond_props['arp_ip_target'])
                    self.assertTrue(expected_string in bond_params,
                                    error_msg.format(expected_string))

                else:
                    expected_string = 'MII Polling Interval (ms): {0}'.format(
                        bond_props.get("miimon", "0"))
                    self.assertTrue(expected_string in bond_params,
                                    error_msg.format(expected_string))
                    expected_string = 'ARP Polling Interval (ms)'
                    self.assertFalse(expected_string in bond_params,
                                     error_msg.format(expected_string))

    @staticmethod
    def get_network_item_script_name(file_type, item_name='*'):
        """
        Description:
        Returns path to a network item's config script

        Args:
        file_type (Str): the network file type i.e. ifcfg,ifup, ifdown

        Kwargs:
        item_name (Str): Name of the item. If none specified,
                   default is * - which returns all files of the
                   specified arg 'file_type'

        Returns (str): Path to config script(s)
        """

        return '{0}/{1}-{2}'.format(const.NETWORK_SCRIPTS_DIR,
                                    file_type, item_name)

    def check_ifcfg_file_on_nodes(self, node, properties):
        """
        Description:
            Checks the ifcfg file on node specified.

        Args:
            node (str): The node to check the ifcfg file on.
            properties (list): List of properties to check that they've been
                          applied to the ifcfg file on the specified node.

        """
        std_err = self.check_ifcfg_bond_props(properties)
        self.assertEqual([], std_err)

        cmd = '{0}{1} | {2} 2001'.format(self.net.get_ifconfig_cmd(),
                                         self.bond_device_name,
                                         const.GREP_PATH)
        out, _, rc = self.run_command(node, cmd)
        self.assertEqual(0, rc)
        self.assertNotEqual([], out)

    def check_ifcfg_bond_props(self, bond_props):
        """
        Description:
            Check bond system configuration

        Args:
            bond_props (list): List of dicts of props of bond item in
                               model

        Returns:
            list. stderr of checking configuration
        """
        errors = []
        for item in bond_props:
            node_url = self.path_dict[item["NODE"]]
            node_fname = self.get_node_filename_from_url(self.ms_node,
                                                         node_url)
            self.log("info", "VERIFYING NODE '{0}'".format(node_fname))

            path = self.get_network_item_script_name("ifcfg")
            dir_contents = self.list_dir_contents(node_fname, path)
            if dir_contents == []:
                errors.append("{0} doesn't exist".format(
                    path))

            path = self.get_network_item_script_name(
                "ifcfg", item_name=item["CONFIG"]["DEVICE"])

            std_out = self.get_file_contents(node_fname, path)

            for prop_name, prop_value in item["CONFIG"].iteritems():
                if "mode" in prop_name or "arp" in prop_name or \
                        "mii" in prop_name:
                    if not self.is_text_in_list(
                            '{0}={1}'.format(prop_name, prop_value),
                            std_out):
                        errors.append('{0}={1} is not configured in file {2} '
                                      'on node {3}'.format(
                            prop_name, prop_value, path, node_fname))
                else:
                    if not self.is_text_in_list(
                            '{0}="{1}"'.format(prop_name, prop_value),
                            std_out):
                        errors.append('{0}="{1}" is not configured in file '
                                      '{2} on node {3}'
                                      .format(prop_name, prop_value, path,
                                              node_fname))
        return errors

    def ping_ips(self, ip_addr_dict, args=''):
        """
        Description: Pings the IP addresses passed in the supplied dictionary
                     on the relevant nodes.

        Args:
            ip_addr_dict (dict): Dictionary of IPv4 and IPv6 IP addresses of
                                 the relevant nodes.

        Kwargs:
            args (str): Optional arguments to append to the ping command.
        """
        for node, ip_info in ip_addr_dict.iteritems():
            for address_type, address in ip_info.iteritems():

                if address_type == "IPV4":
                    cmd = self.net.get_ping_cmd(address, 10, args=args)
                    _, _, rc = self.run_command(node, cmd, su_root=True,
                                                default_asserts=True)
                    self.assertEqual(0, rc)

                elif address_type == "IPV6":
                    cmd = self.net.get_ping6_cmd(address, 10, args=args)
                    _, _, rc = self.run_command(node, cmd, su_root=True,
                                                default_asserts=True)
                    self.assertEqual(0, rc)

    @attr('all', 'revert', 'story13259', 'story13259_tc01')
    def test_01_p_create_update_bond_valid_arp_miimon_props(self):
        """
        @tms_id: litpcds_13259_tc01
        @tms_requirements_id: LITPCDS-13259
        @tms_title: create and update bond with valid arp/miimon properties
        @tms_description: Create/Update a dual-stack bond with valid
            arp/miimon properties so covers litpcds_13259_tc02,
            litpcds_13259_tc03, litpcds_13259_tc04, litpcds_13259_tc05,
            litpcds_13259_tc06.
        @tms_test_steps:
            @step: Find free NIC's on the MS and Peer Nodes
            @result: A free NIC is assigned to each node
            @step: Create network item under '/infrastructure'
            @result: Item created
            @step: Create an eth item on the MS and peer nodes
            @result: Items created
            @step: Create a bond item on the MII bond on MS and arp bond on
                    peer nodes with valid arp properties
            @result: Items created
            @step: Create a cluster-level vcs-network-host item
            @result: Items created
            @step: Register all nodes for cleanup at end of test
            @result: Nodes registered for cleanup at end of test
            @step: Create and Run plan
            @result: Plan executes successfully
            @step: Check /proc/net/bonding/bond13259/ on MS and nodes
            @result: File contains correct information
            @step: Verify correct bond properties have been applied in the
                   ifcfg file on the nodes
            @result: Correct properties applied
            @step: Check bonds are pingable
            @result: Nodes are pingable
            @step: Update arp properties of bond item on MS and peer nodes
            @result: Items updated
            @step: Create new cluster-level vcs-network-host items
            @result: Items created
            @step: Create and Run plan
            @result: Plan executes successfully
            @step: Verify correct properties have been applied in the
                   ifcfg file on the nodes
            @result: Correct properties applied
            @step: Check /proc/net/bonding/bond13259/ on MS and nodes
            @result: File contains correct information
            @step: Delete miimon property of bond item on MS
                   Delete arp_interval arp_ip_target arp_validate arp_all_
                   targets properties of bond item on peer nodes
            @result: Items updated
            @step: Update ms bond to have arp properties
                   Update peer node bond to have properties 'miimon', 'mode=1'
                   and 'device_name' on MS and peer nodes
            @result: Items updated
            @step: Create and Run plan
            @result: Plan executes successfully
            @step: Verify correct properties have been applied in the
                   ifcfg file on the nodes
            @result: Correct properties applied
            @step: Check /sys/class/net/ arp_ip_target file
            @result: File contains correct information
            @step: Check /proc/net/bonding/ file on MS and nodes
            @result: File contains correct information
            @step: Delete arp properties from bond item on peer nodes
                   Delete property 'miimon' from bond item on peer nodes
            @result: Items updated
            @step: Update bonds to have arp properties 'arp_interval'
                   'arp_ip_target''arp_validate' and 'arp_all_targets'
                   on MS and peer nodes
            @result: Items updated
            @step: Create and Run plan
            @result: Plan executes successfully
            @step: Verify correct properties have been applied in the
                   ifcfg file on the nodes
            @result: Correct properties applied
            @step: Check /proc/net/bonding/ file on MS and nodes
            @result: File contains correct information
            @step: Update arp properties 'arp_interval=400' on bond on
                   peer nodes
            @result: Items updated
            @step: Create and Run Plan
            @result: Plan executes successfully
            @step: Verify correct bond properties have been applied in the
                   ifcfg file on the nodes
            @result: Correct properties applied
            @step: Check /proc/net/bonding/ file on MS and nodes
            @result: File contains correct information

            @step: Delete arp_interval arp_ip_target arp_validate arp_all_
                   targets properties of bond item on MS and peer nodes
            @result: Items updated
            @step: Create and Run plan
            @result: Plan executes successfully
            @step: Verify correct properties have been applied in the
                   ifcfg file on the nodes
            @result: Correct properties applied
            @step: Check /proc/net/bonding/ file on MS and nodes
            @result: File contains correct information

        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        # Tests 1-6 below are from the pre-refactored script where they were
        # separate tests

        self.log('info', "# 1. Find free NIC's on the MS and peer nodes")
        node1_eth = network_data.NODE1_ETH
        node1_eth["NODE"] = self.peer_nodes[0]
        node2_eth = network_data.NODE2_ETH
        node2_eth["NODE"] = self.peer_nodes[1]
        node_eths = [node1_eth, node2_eth]

        self.identify_free_nics(self.ms_node, self.node_urls, node_eths,
                                network_data.MN_SERVICES_NICS)

        ms_eth = network_data.MS_ETH
        ms_eth["NODE"] = self.ms_node
        self.identify_free_nics(self.ms_node, [self.ms_url], [ms_eth],
                                network_data.MS_SERVICES_NICS)

        self.log('info', "# 2. Create network item under '/infrastructure'" \
                         "Create an eth item on the MS and peer nodes\n" \
                         "Create a bond item on the MS and peer nodes\n" \
                         "Create cluster-level vcs-network-host items")
        create_network_items = \
            network_data.CREATE_ITEMS_MS + network_data.CREATE_ITEMS_NODES
        for item in create_network_items:
            self.create_update_network_item(self.ms_node, item)

        self.log('info', '# 3. Register all nodes for cleanup at end of test')
        self.reg_cleanup_bond()

        self.log('info', '# 4. Create and Run plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log('info', '# 5. Check /proc/net/bonding/{0}/ on MS and nodes'
                 .format(self.bond_device_name))
        self.check_bond_file()

        self.log('info', '# 6. Verify correct bond properties '
                         'have been applied in the ifcfg file on the nodes')
        bond_items = network_data.BOND_ITEMS
        self.check_ifcfg_file_on_nodes(self.peer_nodes[0], bond_items)

        # ###########################TEST 1################################
        # # Validate a bond can be created with arp properties.

        self.log('info', '# 7. Check bonds are pingable')
        ip_addr_dict = {
            self.ms_node: {
                "IPV4": network_data.NODE2_IP[0],
                "IPV6": network_data.IPV6ADDRESSES[2]},
            self.peer_nodes[0]: {
                "IPV4": network_data.MS_IP[0],
                "IPV6": network_data.IPV6ADDRESSES[1]},
            self.peer_nodes[1]: {
                "IPV4": network_data.NODE1_IP[0],
                "IPV6": network_data.IPV6ADDRESSES[0]}}

        self.ping_ips(ip_addr_dict)

        ##########################TEST 2#################################
        # Validate arp properties can be updated.

        self.log('info', '# 8. Update properties of bond item on MS and ' \
                         'peer nodes\n' \
                         'Create new cluster-level vcs-network-host items')
        for item in network_data.UPDATE_ITEMS:
            self.create_update_network_item(self.ms_node, item,
                                            update=item["UPDATE"])

        self.log('info', '# 9. Create and Run plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log('info', '# 10. Verify correct properties have been applied ' \
                         'in the ifcfg file on the nodes')
        self.check_ifcfg_file_on_nodes(self.peer_nodes[0],
                                       network_data.NEW_BOND_ITEMS)

        self.log('info', '# 11. Check /proc/net/bonding/bond13259/ on MS ' \
                         'and nodes')
        self.check_bond_file()

        ##########################TEST 4#################################
        # Validate that a bond can be updated to use miimon instead of arp.

        self.log('info', "# 12. Delete 'arp_interval' 'arp_ip_target'"
                         "'arp_validate' 'arp_all_targets' properties of "
                         "bond item on MS and peer nodes.")

        remove_arp_bond_props = network_data.DELETE_BOND_PROPS
        for item in remove_arp_bond_props:
            self.create_update_network_item(self.ms_node, item,
                                            action_del=item["DELETE_PROPS"])

        self.log('info', '# 13. Update bond to have properties miimon, '
                         'mode=1 and device_name on MS and peer nodes.')
        update_add_miimon_props = network_data.UPDATE_ADD_BOND_PROPS

        for item in update_add_miimon_props:
            self.create_update_network_item(self.ms_node, item,
                                            update=True)
        self.log('info', '# 14. Create and Run plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log('info', '# 15. Verify correct properties have been ' \
                         'applied in the ifcfg file on the nodes')
        self.check_ifcfg_file_on_nodes(self.peer_nodes[0],
                                       update_add_miimon_props)

        self.log('info', '# 16. Check /sys/class/net/ arp_ip_target file')
        self.check_bond_file(self.bond_arp_ip_target_file)

        self.log('info', '# 17. Check /proc/net/bonding/ file on all nodes')
        self.check_bond_file()

        ###########################TEST 5###############################
        #  Validate that a bond can be updated to use arp instead of miimon

        self.log('info', '# 18. Delete property "miimon" from bond item '
                         'on MS' \
                         '\nUpdate bonds to have arp properties ' \
                         '"arp_interval" "arp_ip_target" "arp_validate" and ' \
                         '"arp_all_targets"')
        remove_miimon_bond_prop = network_data.DELETE_PROP_MIIMON
        for item in remove_miimon_bond_prop + bond_items:
            self.create_update_network_item(self.ms_node, item,
                                            update=True,
                                            action_del=item["DELETE_PROPS"])

        self.log('info', '# 19. Create and Run plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log('info', '# 20. Verify correct properties have been ' \
                         'applied in the ifcfg file on the nodes')
        self.check_ifcfg_file_on_nodes(self.peer_nodes[0],
                                       network_data.ADD_ARP_PROP)

        self.log('info', '# 21. Check /proc/net/bonding/ file on MS and nodes')
        self.check_bond_file()

        #############################TEST 6##################################
        # Validate all other properties on a bond can be updated while
        # arp_all_targets remains set to all.

        self.log('info', "# 22. Update arp properties 'arp_interval=400' "
                         "on bond on peer nodes")
        for item in network_data.UPDATE_ARP_PROPS:
            self.create_update_network_item(self.ms_node, item,
                                            update=item["UPDATE"])

        self.log('info', '# 23. Create and Run Plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log('info', '# 24. Verify correct properties have been ' \
                         'applied in the ifcfg file on the nodes')
        self.check_ifcfg_file_on_nodes(self.peer_nodes[0],
                                       network_data.UPDATE_ARP_PROPS)

        self.log('info', '# 25. Check /proc/net/bonding/ file on MS and nodes')
        self.check_bond_file()

        ##########################TEST 3#################################
        # Verify that arp properties can be removed and then the bond then has
        # neither miimon nor arp properties set.

        self.log('info', "# 26. Delete 'arp_interval' 'arp_ip_target'"
                         "'arp_validate' 'arp_all_targets' properties of "
                         "bond item on MS and peer nodes.")
        remove_arp_bond_props = network_data.DELETE_BOND_PROPS

        for item in remove_arp_bond_props:
            self.create_update_network_item(self.ms_node, item,
                                            action_del=item["DELETE_PROPS"])

        self.log('info', '# 27. Create and Run plan')
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE,
                                plan_timeout_mins=10)

        self.log('info', '# 28. Verify correct properties have been ' \
                         'applied in the ifcfg file on the nodes')
        self.check_ifcfg_file_on_nodes(self.peer_nodes[0],
                                       remove_arp_bond_props)

        self.log('info', '# 29. Check /proc/net/bonding/ file on all nodes')
        self.check_bond_file()

    # attr('pre-reg', 'revert', 'story13259', 'story13259_tc02')
    def obsolete_02_p_update_bond_valid_arp_props(self):
        """
        Test merged with test_01_p_create_update_bond_valid_arp_miimon_props.
        #tms_id: litpcds_13259_tc02
        #tms_requirements_id: LITPCDS-13259
        #tms_title: update bond valid arp props
        #tms_description: Validate that an applied bond can be updated with
                          valid arp properties.
        #tms_test_steps:
            #step: Create network item under 'infrastructure'
            #result: item created
            #step: Create 1 eth item on ms
            #result: item created
            #step: Create 1 bond item on ms
            #result: item created
            #step: Create 1 eth and 1 bond item on node1
            #result: items created
            #step: create cluster level vcs-network-host item
            #result: item created
            #step: Create 1 eth and 1 bond item on node2
            #result: items created
            #step: create second cluster level vcs-network-host item
            #result: item created
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/bond file on nodes
            #result: file contains correct information
            #step: execute ifcfg on nodes
            #result: nodes contain correct information
            #step: update properties of bond item on ms
            #result: item updated
            #step: create third cluster level vcs-network-host item
            #result: item created
            #step: update properties of bond item on node1
            #result: item updated
            #step: create fourth cluster level vcs-network-host item
            #result: item created
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/ file on nodes
            #result: file contains correct information
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """

    # attr('pre-reg', 'revert', 'story13259', 'story13259_tc03')
    def obsolete_03_p_chk_no_default(self):
        """
        Test merged with test_01_p_create_update_bond_valid_arp_miimon_props.
        #tms_id: litpcds_13259_tc03
        #tms_requirements_id: LITPCDS-13259
        #tms_title: verify arp property can be removed
        #tms_description: Validate that arp properties can be removed from
                          an applied bond and that the bond is set with neither
                          miimon nor arp
        #tms_test_steps:
            #step: Create network item under 'infrastructure'
            #result: item created
            #step: Create 1 eth item on ms
            #result: item created
            #step: Create 1 bond item on ms
            #result: item created
            #step: Create 1 eth and 1 bond item on node1
            #result: items created
            #step: create cluster level vcs-network-host item
            #result: item created
            #step: Create 1 eth and 1 bond item on node2
            #result: items created
            #step: create second cluster level vcs-network-host item
            #result: item created
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/bond file on nodes
            #result: file contains correct information
            #step: execute ifcfg on nodes
            #result: nodes contain correct information
            #step: delete arp_interval arp_ip_target arp_validate
                   arp_all_targets properties of bond item on ms, node1 and
                   node 2
            #result: items updated
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/ file on nodes
            #result: file contains correct information
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """

    # attr('pre-reg', 'revert', 'story13259', 'story13259_tc04')
    def obsolete_04_p_replace_arp_with_miimon(self):
        """
        Test merged with test_01_p_create_update_bond_valid_arp_miimon_props.
        #tms_id: litpcds_13259_tc04
        #tms_requirements_id: LITPCDS-13259
        #tms_title: replace arp with miimon o bond item
        #tms_description: Validate that a bond can be update to use miimon
                          instead of arp.
        #tms_test_steps:
            #step: Create network item under 'infrastructure'
            #result: item created
            #step: Create 1 eth item on ms
            #result: item created
            #step: Create 1 bond item on ms
            #result: item created
            #step: Create 1 eth and 1 bond item on node1
            #result: items created
            #step: create cluster level vcs-network-host item
            #result: item created
            #step: Create 1 eth and 1 bond item on node2
            #result: items created
            #step: create second cluster level vcs-network-host item
            #result: item created
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/bond file on nodes
            #result: file contains correct information
            #step: execute ifcfg on nodes
            #result: nodes contain correct information
            #step: delete arp_interval arp_ip_target arp_validate
                   arp_all_targets properties of bond item on ms, node1 and
                   node 2
            #result: items updated
            #step: update miimon, network_name and mode='1' device_name
                   properties of bond items on ms, noe1 and node2
            #result: items updated
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/ file on nodes
            #result: file contains correct information
            #step: check /sys/class/net/ arp_ip_target file
            #result: file contains correct information
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """

    # attr('pre-reg', 'revert', 'story13259', 'story13259_tc05')
    def obsolete_05_p_replace_miimon_with_arp(self):
        """
        Test merged with test_01_p_create_update_bond_valid_arp_miimon_props.
        #tms_id: litpcds_13259_tc05
        #tms_requirements_id: LITPCDS-13259
        #tms_title: replace miimon with arp on bond item
        #tms_description: Validate that a bond can be updated to use arp
                          instead of miimon
        #tms_test_steps:
            #step: Create network item under 'infrastructure'
            #result: item created
            #step: Create 1 eth item on ms
            #result: item created
            #step: Create 1 bond item on ms
            #result: item created
            #step: Create 1 eth and 1 bond item on node1
            #result: items created
            #step: create cluster level vcs-network-host item
            #result: item created
            #step: Create 1 eth and 1 bond item on node2
            #result: items created
            #step: create second cluster level vcs-network-host item
            #result: item created
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/bond file on nodes
            #result: file contains correct information
            #step: execute ifcfg on nodes
            #result: nodes contain correct information
            #step: delete miimon properties of bond items on ms, noe1 and node2
            #result: items updated
            #step: update arp_interval arp_ip_target arp_validate
                   arp_all_targets properties of bond item on ms, node1 and
                   node 2
            #result: items updated
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bond is configured correctly
            #step: check /proc/net/bonding/ file on nodes
            #result: file contains correct information
            #step: check /sys/class/net/ arp_ip_target file
            #result: file contains correct information
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """

    # attr('pre-reg', 'revert', 'story13259', 'story13259_tc06')
    def obsolete_06_p_update_bond_valid_arp_props_arp_all_targets_all(self):
        """
        Test merged with test_01_p_create_update_bond_valid_arp_miimon_props.
        #tms_id: litpcds_13259_tc06
        #tms_requirements_id: LITPCDS-13259
        #tms_title: update bond alid arp props arp all targets all
        #tms_description: Validate that an applied bond can be updated with
                          valid arp properties when arp_all_targets remains set
                          to all.
        #tms_test_steps:
            #step: Create network item under 'infrastructure'
            #result: item created
            #step: Create 1 eth item on ms
            #result: item created
            #step: Create 1 bond item on ms
            #result: item created
            #step: Create 1 eth and 1 bond item on node1
            #result: items created
            #step: create cluster level vcs-network-host item
            #result: item created
            #step: Create 1 eth and 1 bond item on node2
            #result: items created
            #step: create second cluster level vcs-network-host item
            #result: item created
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bridge is configured correctly
            #step: check /proc/net/bonding/bond file on nodes
            #result: file contains correct information
            #step: execute ifcfg on nodes
            #result: nodes contain correct information
            #step: update ms bond item properties except arp_all_targets
            #result: item updated
            #step: update node1 bond item properties except arp_all_targets
            #result: item updated
            #step: create third cluster level vcs-network-host item
            #result: item created
            #step: update node2 bond item properties except arp_all_targets
            #result: item updated
            #step: create fourth cluster level vcs-network-host item
            #result: item created
            #step: create and run plan
            #result: plan executes successfully
            #step: execute ifcfg on nodes
            #result: bond is configured correctly
            #step: check /proc/net/bonding/ file on nodes
            #result: file contains correct information
            #step: check /sys/class/net/ arp_ip_target file
            #result: file contains correct information
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
