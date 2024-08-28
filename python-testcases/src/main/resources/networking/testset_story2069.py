"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     August 2014
@author:    Kieran Duggan, Matt Boyer, Mary Russel, Igor Milovanovic
@summary:   Integration
            Agile: STORY-2069
"""
import netaddr
from litp_generic_test import GenericTest, attr
from networking_utils import NetworkingUtils
import test_constants as const


class Story2069(GenericTest):
    """
    As a LITP User, I want link aggregation (bonding) so that I can
    achieve higher network bandwidth and/or redundancy
    """
    test_ms_if1 = None
    test_ms_if2 = None
    test_node_if1 = None
    test_node_if2 = None
    test_node2_if1 = None
    test_node2_if2 = None

    def setUp(self):
        """
        Runs before every single test
        """
        # 1. Call super class setup
        super(Story2069, self).setUp()
        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.all_nodes = self.peer_nodes + [self.ms_node]

        self.ms_url = "/ms"
        self.node_urls = self.find(self.ms_node, "/deployments", "node")
        self.all_node_urls = self.node_urls + [self.ms_url]

        self.net = NetworkingUtils()

        # COMMON VALUES
        self.bond_name = 'bond2069'
        self.test1_first_ip = '10.10.10.1'

        # GET NETWORKS PATH
        self.networks_path = self.find(self.ms_node, "/infrastructure",
                                                        "network", False)[0]
        self.ms_net_if = self.find(self.ms_node, self.ms_url,
                                        "collection-of-network-interface")[0]

    def tearDown(self):
        """
        Run after each test and performs the following:
        """
        # 2. call teardown
        super(Story2069, self).tearDown()

    def check_ifcfg_bond_props(self, bond_props, node_urls):
        """
        Description:
            Asserts correct bond props are in ifconfig files on nodes
        Args:
            vlan_props (list): vlan input properties
            node_urls (list): all nodes to be configured
        Results:
            stderr of checking configuration
        """
        errors = []

        for bond_prop in bond_props:
            for node_url in node_urls:
                self.log("info", "VERIFYING NODE {0}".format(node_url))
                node_fname = self.get_node_filename_from_url(self.ms_node,
                                                                    node_url)

                # CHECK BOND CONFIG FILE EXISTS
                device_name = bond_prop["device_name"]
                path = "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                                    device_name)
                dir_contents = self.list_dir_contents(node_fname, path)
                if [] == dir_contents:
                    errors.append("ifcfg-{0} doesn't exist".format(
                                                    device_name))

                # CHECK BOND FILE CONTENT
                std_out = self.get_file_contents(node_fname, path)
                device = 'DEVICE="{0}"'.format(device_name)

                if not self.is_text_in_list(device, std_out):
                    errors.append("{0} is not configured".format(device))

                if 'mode' in bond_props:
                    if not self.is_text_in_list(
                            "mode={0}".format(bond_prop["mode"]), std_out):
                        errors.append("MODE is not configured")

                if 'miimon' in bond_props:
                    if not self.is_text_in_list(
                            "miimon={0}".format(bond_prop["miimon"]), std_out):
                        errors.append("MIIMON is not configured")

                if 'ipaddress' in bond_props:
                    ipaddress = bond_prop["ipaddress"]
                    if not self.is_text_in_list(
                            'IPADDR="{0}"'.format(ipaddress), std_out):
                        errors.append("IPADDR={0} is not configured".format(
                                                                    ipaddress))

                if 'ipv6address' in bond_props:
                    ip6address = bond_prop["ipv6address"]
                    if not self.is_text_in_list(
                            'IPV6ADDR="{0}"'.format(ip6address), std_out):
                        errors.append("IPV6ADDR={0} is not configured".format(
                                                                ip6address))

        return errors

    def reg_cleanup_bond(self):
        """
        Description:
            Register the nodes for cleanup of bonds
        """
        for node in self.all_nodes:
            self.add_nic_to_cleanup(node, self.bond_name, is_bond=True)

    def create_network(self, net_name, subnet, url):
        """
        Description:
            Creates a network using the specified information
        Args:
            net_name(str): The name of the network
            subnet(str): The subnet of the network
            url(str): Unique name for the item in the litp model
        """
        network_url = self.networks_path + "/" + url
        props = "name='{0}' subnet='{1}'".format(net_name, subnet)
        self.execute_cli_create_cmd(self.ms_node, network_url, "network",
                                                                        props)

    def create_eth(self, node_url, if_data, url="if_2069"):
        """
        Description:
            Creates an eth item using the specified information
        Args:
            node_url(str): Path of the node the items are being made on
            if_data(dict): Information of the nic to be used
        KwArgs:
            url(str): Unique name for the eth item in the litp model. Default
                is if_2069
        """
        net_if_url = self.find(self.ms_node, node_url,
                                        "collection-of-network-interface")[0]
        node_if_url = net_if_url + "/" + url

        eth_props = "macaddress='{0}' device_name='{1}' master='{2}'".format(
                                                            if_data["MAC"],
                                                            if_data["NAME"],
                                                            self.bond_name)
        self.execute_cli_create_cmd(self.ms_node, node_if_url, "eth",
                                                                    eth_props)

    def create_bond(self, node_url, network_name, ipaddress, ip6address=None):
        """
        Description:
            Creates eth and bond item using the provided properties
        Args:
            node_url(str): Path of the node the items are being made on
            network_name(str): The name of the network the bond will use
            ipaddress(IPaddress): IP4 address to be used for bond
        KwArgs:
            ip6address(IPaddress): IP6 address to be used for bond. Defaults
                to None
        """
        net_if_url = self.find(self.ms_node, node_url,
                                        "collection-of-network-interface")[0]
        node_bond_url = net_if_url + "/b_2069"

        bond_props = "device_name='{0}' ipaddress='{1}'" \
                     " network_name='{2}' mode='1' miimon='100'".format(
                                                                self.bond_name,
                                                                ipaddress,
                                                                network_name)
        if ip6address:
            bond_props += " ipv6address='{0}'".format(ip6address)

        self.execute_cli_create_cmd(self.ms_node, node_bond_url, "bond",
                                    bond_props)

    def check_ifcfg(self, bond_url, nodes_to_verify):
        """
        Description:
            Ensures ifcfg-bondX is configured correctly
        Args:
            bond_url(str): Litp path of item to check
            nodes_to_verify(list): List of nodes to verify ifcfg on
        """
        props = self.get_props_from_url(self.ms_node, bond_url)
        std_err = self.check_ifcfg_bond_props([props], nodes_to_verify)
        self.assertEqual([], std_err)

    def check_bond_file(self, contents, file_name="bond2069"):
        """
        Description:
            Checks specified bond file for expected contents
        Args:
            contents(list): The lines expected to be found in the file
        KwArgs:
            file_name(str): The name of the file to check. Default is bond2069
        """
        bond_params = self.get_file_contents(self.ms_node,
                                            "/proc/net/bonding/" + file_name)
        for line in contents:
            self.assertTrue(line in bond_params,
                            "Expected line '{0}' not in bond params".format(
                                                                        line))

    #@attr('all', 'revert', 'story2069', 'story2069_tc01')
    def obsolete_01_n_create_bond_without_slave(self):
        """
        Converted to AT "test_01_n_create_bond_without_slave.at" in network
        #tms_id: litpcds_2069_tc01
        #tms_requirements_id: LITPCDS-2069
        #tms_title: Create bond without slave
        #tms_description: Verify creating a which has no slave result in an
            error being thrown when creating a plan property values.
        #tms_test_steps:
        #step: Create eth item under "infrastructure"
        #result: Item created
        #step: Create bond item on ms
        #result: Item created
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: is not a master
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', '2069')
    def obsolete_02_p_create_bond_with_single_slave(self):
        """
        Description:
            Create a bond item which only has one slave
            This test was merged with TC21
        Steps:
            1.Create a bond item with device_name=bondX
            2.Create two 'eth' with master=bondX
            3.Create and run plan
            4.Plan should complete successfully
            5.Check that ifcfg-bondX and /proc/net/bonding/bondX are
            configured correctly
        """
        pass

    @attr('all', 'revert', 'story2069', 'story2069_tc03', 'cdb_priority1',
          'physical')
    def test_03_p_create_bond_with_multiple_slaves(self):
        """
        @tms_id: litpcds_2069_tc03
        @tms_requirements_id: LITPCDS-2069
        @tms_title: Create bond with multiple slaves
        @tms_description: Verify create bond with multiple slaves
            will result in a successful plan
        @tms_test_steps:
        @step: Create network item under "infrastructure"
        @result: Item created
        @step: Create two eth items and one bond item on ms, node1 and node2
        @result: Item created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute ifcfg on bond items
        @result: Information returned is correct
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Setup networks required for test")
        self.create_network("test1", "10.10.10.0/24", "test_network2069")

        self.log('info', "2. Find free nics")
        free_nics = self.verify_backup_free_nics(self.ms_node, self.ms_url,
                                                        required_free_nics=2)
        self.test_ms_if1 = free_nics[0]
        self.test_ms_if2 = free_nics[1]

        free_nics = self.verify_backup_free_nics(self.ms_node,
                                                    self.node_urls[0],
                                                    required_free_nics=2)
        self.test_node_if1 = free_nics[0]
        self.test_node_if2 = free_nics[1]

        free_nics = self.verify_backup_free_nics(self.ms_node,
                                                    self.node_urls[1],
                                                    required_free_nics=2)
        self.test_node2_if1 = free_nics[0]
        self.test_node2_if2 = free_nics[1]

        self.log('info', "3. Create eth and bond")
        net_name = "test1"
        ipaddress = netaddr.IPAddress(self.test1_first_ip)

        self.create_eth(self.ms_url, self.test_ms_if1)
        self.create_eth(self.ms_url, self.test_ms_if2, "if_2070")
        self.create_bond(self.ms_url, net_name, ipaddress)

        ipaddress += 1

        self.create_eth(self.node_urls[0], self.test_node_if1)
        self.create_eth(self.node_urls[0], self.test_node_if2, "if_2070")
        self.create_bond(self.node_urls[0], net_name, ipaddress)

        ipaddress += 1

        self.create_eth(self.node_urls[1], self.test_node2_if1)
        self.create_eth(self.node_urls[1], self.test_node2_if2, "if_2070")
        self.create_bond(self.node_urls[1], net_name, ipaddress)

        self.reg_cleanup_bond()

        self.log('info', "4. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        # Check that ifcfg-bondX is configured correctly
        bond_ms_url = self.ms_net_if + "/b_2069"
        self.check_ifcfg(bond_ms_url, self.all_node_urls)

    #@attr('all', 'revert', 'story2069', 'story2069_tc04')
    def obsolete_04_n_create_bonded_interface_with_vlan(self):
        """
        Converted to AT "test_04_n_create_bonded_interface_with_vlan.at" in
            network
        #tms_id: litpcds_2069_tc04
        #tms_requirements_id: LITPCDS-2069
        #tms_title: Create bonded interface with vlan
        #tms_description: Verify creating bonded interface with vlan
            is not supported
        #tms_test_steps:
        #step: Create network item under "infrastructure"
        #result: Item created
        #step: Create one eth items, one bond item and one eth item on ms
        #result: Item created
        #step: create plan
        #result: message shown: Bonded and VLAN tagged; this is not currently
            supported
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2069', 'story2069_tc05')
    def obsolete_05_n_create_bonded_interface_with_bridge(self):
        """
        This test is obsolete due to functionality delivered in LITPCDS-6629
        Description:
            Create a bonded interface with a bridge item type defined
        Steps:
            1. Create a bond which has bridge=brX
            2. Check error message returned at Item Creation
        """
        pass

    @attr('all', 'revert', 'story2069', 'story2069_tc09')
    def test_09_p_create_bond_with_vlan(self):
        """
        @tms_id: litpcds_2069_tc09
        @tms_requirements_id: LITPCDS-2069
        @tms_title: Create bond with vlan
        @tms_description: Verify creating bond with vlan results in a
            successful plan. This test now covers litpcds_2069_tc03,
            litpcds_2069_tc18 and litpcds_2069_tc21
        @tms_test_steps:
        @step: Create two network item under "infrastructure"
        @result: Items created
        @step: Create two eth items and one bond item on node1, node2 and
            the ms
        @result: Items created
        @step: Create one vlan item on ms
        @result: Item created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute ifcfg on bond item
        @result: Information returned is correct
        @step: Fix up bonds and make sure bonds are pingable
        @result: Bonds are pingable
        @step: Update bond items properties on node1, node2 and ms
        @result: Items updated
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute ifcfg-bond on each node
        @result: Bonds are configured correctly
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Setup networks required for test")
        self.create_network("test1", "10.10.10.0/24", "test_network2069")
        self.create_network("test2", "14.14.14.0/24", "test_2069_n2")

        self.log('info', "2. Find free nics")
        self.test_ms_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.ms_url)[0]

        self.test_node_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.node_urls[0])[0]

        self.test_node2_if1 = self.verify_backup_free_nics(self.ms_node,
                                                        self.node_urls[1])[0]

        node_nic_info = [
            (self.node_urls[0], self.test_node_if1),
            (self.node_urls[1], self.test_node2_if1),
            (self.ms_url, self.test_ms_if1)
        ]

        self.log('info', "3. Create eth, bond and vlan")
        vlan_id = 2069
        bond_ms_url = "{0}/b_{1}".format(self.ms_net_if, vlan_id)
        vlan_url = "{0}/vlan_{1}".format(self.ms_net_if, vlan_id)

        ipv4 = "10.10.10.1"
        ipv6 = '2001:abcd:ef::11'
        ipaddress = netaddr.IPAddress(ipv4)
        ipv6address = netaddr.IPAddress(ipv6)
        ipaddress2 = netaddr.IPAddress("14.14.14.1")

        for node_and_ifs in node_nic_info:
            self.create_eth(node_and_ifs[0], node_and_ifs[1])
            self.create_bond(node_and_ifs[0], "test1", ipaddress, ipv6address)
            ipaddress += 1
            ipv6address += 1

        vlan_props = "device_name='{0}.{1}' ipaddress='{2}' " \
                     "network_name='test2'".format(self.bond_name,
                                                        vlan_id, ipaddress2)
        self.execute_cli_create_cmd(self.ms_node, vlan_url, "vlan", vlan_props)

        self.reg_cleanup_bond()

        self.log('info', "4. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "5. Validate sysconfig and bonding files")
        self.check_ifcfg(bond_ms_url, self.all_node_urls)
        bond_params = ['Bonding Mode: fault-tolerance (active-backup)']
        self.check_bond_file(bond_params)

        self.log('info', "6. Wait for puppet to kick in and fix up the bonds")
        ifconfig_cmd = self.net.get_ifconfig_cmd("bond2069")
        cmd = '{0} | {1} 2001'.format(ifconfig_cmd, const.GREP_PATH)
        self.run_command(self.peer_nodes[0], cmd, default_asserts=True)

        self.log('info', "7. Check that the bonds are pingable")
        ipaddress = netaddr.IPAddress(ipv4)
        ipv6address = netaddr.IPAddress(ipv6)
        for node in self.all_nodes:
            cmd = self.net.get_ping6_cmd(ipv6address, 10)
            _, _, rc = self.run_command(node, cmd)
            self.assertEqual(0, rc)

            cmd = self.net.get_ping_cmd(ipaddress, 10)
            _, _, rc = self.run_command(node, cmd)
            self.assertEqual(0, rc)

            ipaddress += 1
            ipv6address += 1

        self.log('info', "8. Update bond on each node")
        bond_props = "device_name='{0}' mode='2' miimon='200'"\
                     " network_name='test1'".format(self.bond_name)

        self.execute_cli_update_cmd(self.ms_node, bond_ms_url, bond_props)

        bond_props += " ipaddress='{0}' ipv6address='{1}'"

        ipv6address = netaddr.IPAddress('2001:abcd:ef::21')
        ipaddress = netaddr.IPAddress("10.10.10.71")

        for node in self.node_urls:
            net_if_url = self.find(self.ms_node, node,
                                        "collection-of-network-interface")[0]
            node_bond_url = net_if_url + "/b_2069"

            node_bond_props = bond_props.format(ipaddress, ipv6address)
            self.execute_cli_update_cmd(self.ms_node, node_bond_url,
                                                            node_bond_props)
            ipv6address += 1
            ipaddress += 1

        self.reg_cleanup_bond()

        self.log('info', "9. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "10. Check that ifcfg-bondX is configured correctly")
        self.check_ifcfg(bond_ms_url, self.all_node_urls)

    #@attr('all', 'revert', 'story2069', 'story2069_tc10')
    def obsolete_10_n_create_bonded_eth_invalid_master(self):
        """
        Converted to AT "test_10_n_create_bonded_eth_invalid_master.at" in
        network
        #tms_id: litpcds_2069_tc10
        #tms_requirements_id: LITPCDS-2069
        #tms_title: Create bond with vlan
        #tms_description: Verify eth item with invalid bond name
            results in an error
        #tms_test_steps:
        #step: Create one network item under "infrastructure"
        #result: Item created
        #step: Create one eth items with invalid bond name and one bond item
        #result: Items created
        #step: Create plan
        #result: message shown: Create plan failed: eth ,'master" "bondinvalid"
            is ', ' not a valid Bond "device_name
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2069', 'story2069_tc12')
    def obsolete_12_n_create_bond_non_unique_device_name(self):
        """
        Converted to AT "test_12_n_create_bond_non_unique_device_name.at" in
        network
        #tms_id: litpcds_2069_tc12
        #tms_requirements_id: LITPCDS-2069
        #tms_title: Create bond non unique device name
        #tms_description: Verify two bond items with same device_name value
            results in an error
        #tms_test_steps:
        #step: Create two network items under "infrastructure"
        #result: Items created
        #step: Create two bond  items with the same device_name property value
        #result: Items created
        #step: Create plan
        #result: message shown: 'Create plan failed: Interface ',
            'with device_name "bond2069" is ','not unique.'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2069', 'story2069_tc15')
    def obsolete_15_n_create_bond_without_ip(self):
        """
        Converted to AT "test_15_n_create_bond_without_ip.at" in network
        #tms_id: litpcds_2069_tc15
        #tms_requirements_id: LITPCDS-2069
        #tms_title: Create bond without ip
        #tms_description: Verify creating a bond item with no ipaddress
            property results in an error at create plan
        #tms_test_steps:
        #step: Create one network item under "infrastructure"
        #result: Item created
        #step: Create one bond item1 with no ipaddress property
        #result: Items created
        #step: Create plan
        #result: message shown: 'Create plan failed:',
            ''interface does not define '','an IPv4 address'
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # @attr('all', 'revert', '2069')
    def obsolete_16_p_create_bond_with_ipaddress(self):
        """
        Description:
            Made obsolete as TC was merged with TC18
            Create a bond with a valid ipaddress.
        Steps:
            1. Create a bond with ipaddress and network_name set
            2. Create and run plan
            3. Check that ifcfg-bondX and /proc/net/bonding/bondX are
            configured correctly
            4. Check that the bond is pingable
        """
        pass

    # @attr('all', 'revert', '2069', '2069_17')
    def obsolete_17_p_create_bond_with_ipv6address(self):
        """
        Description:
            Create a bond with a valid ip6address.
            Made obsolete as TC was merged with TC18
        Steps:
            1. Create a bond with ipv6address and network_name set
            2. Check that bond item is created successfully
            3. Create and run plan
            4. Plan should complete successfully
            3. Check that ifcfg-bondX and /proc/net/bonding/bondX are
            configured correctly
            4. Check that the bond is pingable
        """
        pass

    #@attr('pre-reg', 'revert', 'story2069', 'story2069_tc18')
    def obsolete_18_p_create_bond_with_ipaddress_and_ipv6address(self):
        """
        Merged with TC09
        #tms_id: litpcds_2069_tc18
        #tms_requirements_id: LITPCDS-2069
        #tms_title: Create a dual-stack IPv4 + IPv6 bond
        #tms_description: Verify creating a bond item with IPv4 + IPv6
             properties results in a successful plan
        #tms_test_steps:
        #step: Create two network items under "infrastructure"
        #result: Items created
        #step: Create one bond item and one eth item on ms node1, and node2
            with both ipv4 and ipv6
        #result: Items created
        #step: Create and run plan
        #result: Plan executes successfully
        #step: Execute ping command all node1, node2 and ms bonds
        #result: Bonds are pingable
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'revert', 'story2069', 'story2069_tc21')
    def obsolete_21_p_create_bond_update_all_props(self):
        """
        Merged with "test_09_p_create_bond_with_vlan"
        #tms_id: litpcds_2069_tc21
        #tms_requirements_id: LITPCDS-2069
        #tms_title: create bond update all props
        #tms_description:  Validate that updates are made to an applied
            bond's properties
        #tms_test_steps:
        #step: Create one network items under "infrastructure"
        #result: Items created
        #step: Create one bond item and one eth item on ms
        #result: Items created
        #step: Create one bond item and one eth item on node1
        #result: Items created
        #step: Create one bond item and one eth item on node2
        #result: Items created
        #step: Create and run plan
        #result: Plan executes successfully
        #step: Execute ifcfg-bond on each node
        #result: Bonds are configured correctly
        #step: Update bond items properties on node1, node2 and ms
        #result: Items updated
        #step: Create and run plan
        #result: Plan executes successfully
        #step: Execute ifcfg-bond on each node
        #result: Bonds are configured correctly
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

     # @attr('all', 'revert', '2069')
    def obsolete_23_n_validate_miimon_property(self):
        """
        Description:
            Test update of 'miimon' property as well as property validation
        Steps:
            1. Create a 'bond' with no 'miimon' property set
            2. Check that 'miimon' default value = 100
            3. Update miimon property = 0 (minimum value)
            4. Item should be created
            5. Updated miimon property = 999(maximum value)
            6. Item should be created
            7. Updated miimon property = 1000
            8. Check for error at item creation
            9. Updated miimon property = -1
            10. Check for error at item creation
       """
        pass

    #attr('pre-reg', 'revert', 'story2069', 'story2069_tc25', 'physical')
    def obsolete_25_n_validate_eth_master_property(self):
        """
        Converted to AT "test_25_n_validate_eth_master_property.at" in network
        #tms_id: litpcds_2069_tc25
        #tms_requirements_id: LITPCDS-2069
        #tms_title: validate eth master property
        #tms_description: Validate that update of 'master' property on eth
            results in an error
        #tms_test_steps:
        #step: Create one network items under "infrastructure"
        #result: Items created
        #step: Create one bond item and one eth item on ms
        #result: Items created
        #step: Create and run plan
        #result: Plan executes successfully
        #step: Execute ifcfg-bond on ms
        #result: Bond is configured correctly
        #step: Create one eth item with invalid bond property value
        #result: Items created
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: Invalid value
        #step: Create one eth item with invalid bond property value
        #result: Items created
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: is not a valid Bond "device_name"
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'revert', 'story2069', 'story2069_tc28', 'physical')
    def test_28_p_add_extra_interface_to_existing_bond(self):
        """
        @tms_id: litpcds_2069_tc28
        @tms_requirements_id: LITPCDS-2069
        @tms_title: add extra interface to existing bond
        @tms_description: Verify creating a bond and apply it then
            adding an interface to that bond results in a successful plan
        @tms_test_steps:
        @step: Create one network items under "infrastructure"
        @result: Items created
        @step: Create one bond item and one eth item on ms
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute ifcfg-bond on ms
        @result: Bond is configured correctly
        @step: Create one eth item
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute ifcfg-bond on ms
        @result: Bond is configured correctly
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Setup networks required for test")
        self.create_network("test1", "10.10.10.0/24", "test_network2069")

        free_nics = self.verify_backup_free_nics(self.ms_node, self.ms_url,
                                         required_free_nics=2)
        self.test_ms_if1 = free_nics[0]
        self.test_ms_if2 = free_nics[1]

        self.log('info', "2. Create eth and bond")
        ipaddress = netaddr.IPAddress("10.10.10.1")
        self.create_eth(self.ms_url, self.test_ms_if1)
        self.create_bond(self.ms_url, "test1", ipaddress)

        self.reg_cleanup_bond()

        self.log('info', "3. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "4. Validate sysconfig and bonding files")
        bond_ms_url = self.ms_net_if + "/b_2069"
        self.check_ifcfg(bond_ms_url, [self.ms_url])

        bond_params = [
            'Bonding Mode: fault-tolerance (active-backup)',
            'Permanent HW addr: {0}'.format(self.test_ms_if1['MAC'].lower())
        ]
        self.check_bond_file(bond_params)

        self.log('info', "5. Create another eth item")
        self.create_eth(self.ms_url, self.test_ms_if2, "other_if_2069")

        self.reg_cleanup_bond()

        self.log('info', "6. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "7. Validate sysconfig and bonding files")
        self.check_ifcfg(bond_ms_url, [self.ms_url])

        bond_params = [
            'Bonding Mode: fault-tolerance (active-backup)',
            'Permanent HW addr: {0}'.format(self.test_ms_if2['MAC'].lower())
        ]
        self.check_bond_file(bond_params)

    @attr('all', 'revert', 'story2069', 'story2069_tc29', 'physical')
    def test_29_p_remove_bond_and_all_slaves(self):
        """
        @tms_id: litpcds_2069_tc29
        @tms_requirements_id: LITPCDS-2069
        @tms_title: remove_bond_and_all_slaves
        @tms_description: Verify removing a bond and its slaves results in a
            successful plan. This test now also covers litpcds_2069_tc30
        @tms_test_steps:
        @step: Create one network items under "infrastructure"
        @result: Items created
        @step: Create one bond item and two eth items on ms
        @result: Items created
        @step: Create and run plan
        @result: Plan executes successfully
        @step: Execute ifcfg-bond on ms
        @result: Bond is configured correctly
        @step: Remove one eth item on ms
        @result: Items set to forRemoval
        @step: Create plan
        @result: error thrown: ValidationError
        @result: message shown: Create plan failed: All eth peers of and
            slaves of Bond must be removed
        @step: Remove two eth item on ms
        @result: Items set to forRemoval
        @step: Create plan
        @result: error thrown: ValidationError
        @result: message shown: Create plan failed: 'Bond is not a master for
            any eth devices
        @step: Remove one bond item
        @result: Item set to forRemoval
        @step: Create and run plan
        @result: Plan executes successfully
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        self.log('info', "1. Setup networks required for test")
        self.create_network("test1", "10.10.10.0/24", "test_network2069")
        free_nics = self.verify_backup_free_nics(self.ms_node, self.ms_url,
                                                    required_free_nics=2)
        self.test_ms_if1 = free_nics[0]
        self.test_ms_if2 = free_nics[1]

        self.log('info', "2. Find the initial amount of interfaces")
        model_items, _, _ = self.execute_cli_show_cmd(self.ms_node,
                                                    self.ms_net_if + " -l")
        model_items = [vpath for vpath in model_items if vpath.startswith('/')
                                                and self.ms_net_if != vpath]
        initial_if_count = len(model_items)

        self.log('info', "3. Create eth, bond and vlan")
        ipaddress = netaddr.IPAddress("10.10.10.1")

        self.create_eth(self.ms_url, self.test_ms_if1)
        self.create_eth(self.ms_url, self.test_ms_if2, "other_if_2069")
        self.create_bond(self.ms_url, "test1", ipaddress)

        self.reg_cleanup_bond()

        self.log('info', "4. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "5. Check bond file")
        bond_params = [
            'Permanent HW addr: {0}'.format(self.test_ms_if1['MAC'].lower()),
            'Permanent HW addr: {0}'.format(self.test_ms_if2['MAC'].lower())
        ]
        self.check_bond_file(bond_params)

        self.log('info', "6. Remove one of the slave interfaces")
        if_url = self.ms_net_if + "/if_2069"
        self.execute_cli_remove_cmd(self.ms_node, if_url)
        _, stderr, _ = self.execute_cli_createplan_cmd(self.ms_node,
                                                       expect_positive=False)
        self.assertTrue(
            self.is_text_in_list(
                'ValidationError    '
                'Create plan failed: '
                'Bond "bond2069" does not have state ',
                stderr))

        self.assertTrue(
            self.is_text_in_list(
                'ValidationError    '
                'Create plan failed: All eth peers of "{0}" and slaves of '
                'Bond "bond2069" must be removed '.format(
                    self.test_ms_if1['NAME']),
                stderr))

        self.log('info', "7. Remove the other interface")
        other_if_url = self.ms_net_if + "/other_if_2069"
        self.execute_cli_remove_cmd(self.ms_node, other_if_url)
        _, stderr, _ = self.execute_cli_createplan_cmd(self.ms_node,
                                                       expect_positive=False)
        self.assertTrue(self.is_text_in_list('ValidationError    '
                                             'Create plan failed: '
                                             'Bond "bond2069" is '
                                             'not a master for any '
                                             '"eth" devices', stderr))

        self.log('info', "8. Remove the bond")
        bond_ms_url = self.ms_net_if + "/b_2069"
        self.execute_cli_remove_cmd(self.ms_node, bond_ms_url)

        self.log('info', "9. Create and run plan")
        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "10. Check that the items are gone from the model")
        model_items, _, _ = self.execute_cli_show_cmd(
            self.ms_node, self.ms_net_if + " -l")
        model_items = [vpath for vpath in model_items if vpath.startswith('/')
                                                and self.ms_net_if != vpath]
        self.assertEquals(initial_if_count, len(model_items))
        self.assertFalse(if_url in model_items)
        self.assertFalse(other_if_url in model_items)
        self.assertFalse(bond_ms_url in model_items)

        bond_params = [
            'Permanent HW addr: {0}'.format(self.test_ms_if1['MAC'].lower()),
            'Permanent HW addr: {0}'.format(self.test_ms_if2['MAC'].lower())
        ]
        self.check_bond_file(bond_params)

    #@attr('pre-reg', 'revert', 'story2069', 'story2069_tc30', 'physical')
    def obsolete_30_n_remove_slave_and_leave_bond(self):
        """
        Merged with TC29
        #tms_id: litpcds_2069_tc30
        #tms_requirements_id: LITPCDS-2069
        #tms_title: remove slave and leave bond
        #tms_description: Verify removing a bonds slaves results in a error
            when creating a plan
        #tms_test_steps:
        #step: Create one network items under "infrastructure"
        #result: Items created
        #step: Create one bond item and two eth items on ms
        #result: Items created
        #step: Create and run plan
        #result: Plan executes successfully
        #step: Execute ifcfg-bond on ms
        #result: Bond is configured correctly
        #step: Remove one eth item on ms
        #result: Items set to forRemoval
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: Create plan failed: All eth peers of and
            slaves of Bond must be removed
        #step: Remove two eth item on ms
        #result: Items set to forRemoval
        #step: Create plan
        #result: error thrown: ValidationError
        #result: message shown: Create plan failed: 'Bond is not a master for
            any eth devices
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass
