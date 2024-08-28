"""
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     April 2014
@author:    Mary Russell, Boyan Mihovski
@summary:   Integration
            Agile: STORY-56
"""
import netaddr
from litp_generic_test import GenericTest, attr
from networking_utils import NetworkingUtils
import test_constants as const


class Story56(GenericTest):
    """
    As a Network Administrator I want Network routes to be modeled
    independently from IP ranges so that I can configure multiple local
    and remote networks without routing conflicts.
    """
    test_ms_if1 = None
    test_node_if1 = None

    def setUp(self):
        """
        Runs before every single test
        """
        # 1. Call super class setup
        super(Story56, self).setUp()

        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.peer_nodes = self.get_managed_node_filenames()
        self.all_nodes = self.peer_nodes + [self.ms_node]

        self.ms_url = "/ms"
        self.node_urls = self.find(self.ms_node, "/deployments", "node")
        self.all_node_urls = self.node_urls + [self.ms_url]

        self.net = NetworkingUtils()

    def tearDown(self):
        """
        Description:
            Run after each test and performs the following:
        Actions:
            1. Cleanup after test if global results value has been used
            2. Call the superclass teardown method
        Results:
            Items used in the test are cleaned up and the
            super class prints out end test diagnostics
        """
        # 1. call teardown
        super(Story56, self).tearDown()

        # DECONFIGURE test interface
        if self.test_ms_if1:
            cmd = "{0} {1}".format(const.IFDOWN_PATH, self.test_ms_if1["NAME"])
            self.run_command(self.ms_node, cmd, su_root=True)

        if self.test_node_if1:
            for node in self.peer_nodes:
                cmd = "{0} {1}".format(const.IFDOWN_PATH,
                                                    self.test_node_if1["NAME"])
                self.run_command(node, cmd, su_root=True)

    def get_default_route_url(self, node_url):
        """
        Description:
            Returns LITP path of route with subnet 0.0.0.0 under the given
            node path or None if no such route is found
        Args:
            node_url(str): The path of the node to search for the route on
        Returns:
            (str)Default route url
        """
        # GET NETWORK ROUTES
        routes = self.find(self.ms_node, node_url, "route")

        for route_url in routes:
            props = self.get_props_from_url(self.ms_node, route_url)
            if props["subnet"] == "0.0.0.0/0":
                return route_url

        return None

    def select_non_mgmt_route_eth_network(self):
        """
        Description:
            Finds a route, network and interfaces which can be used for
            update tasks in other tests.
        Returns:
            (str, str, list) Returns a valid network(selected_network), a valid
            route(selected_route) and a list of devices(non_mng_if_urls)
        """
        # find non-mgmt/non hb network
        # find route on non-mgmt/non hb network
        net_urls = []
        routes = []

        network_urls = self.find(self.ms_node, "/infrastructure", "network")
        route_urls = self.find(self.ms_node, "/infrastructure", "route")
        for url in network_urls:
            net_props = self.get_props_from_url(self.ms_node, url)
            if 'mgmt' not in net_props['name'] \
                    and 'hb' not in net_props['name']:
                for route in route_urls:
                    route_props = self.get_props_from_url(self.ms_node, route)
                    if 'subnet' in route_props \
                            and route_props["subnet"] != "0.0.0.0/0":
                        routes.append(route)
                        net_urls.append(url)

        # Get eth paths
        non_mng_if_urls = []
        net_props = self.get_props_from_url(self.ms_node, net_urls[0])

        for node_url in self.node_urls:
            if_urls = self.find_children_of_collect(self.ms_node, node_url,
                                                    "network-interface")
            for url in if_urls:
                url_props = self.get_props_from_url(self.ms_node, url)
                if 'subnet' in net_props \
                        and 'network_name' in url_props \
                        and 'hb' not in url_props['network_name'] \
                        and 'mgmt' not in url_props['network_name'] \
                        and net_props["subnet"] != "0.0.0.0/0":
                    non_mng_if_urls.append(url)
                    break

        # Get valid route
        total_nodes_num = len(self.node_urls)
        selected_route = None
        for route_path in routes:
            if route_path is not None:
                resource_node = \
                    self.get_nodes_using_resource(self.ms_node,
                                                  route_path, 'route')
            if len(resource_node) == total_nodes_num:
                selected_route = route_path
                break
        self.assertNotEqual(None, selected_route)

        # Get valid network
        selected_network = None
        for net in network_urls:
            net_props_selected = self.get_props_from_url(self.ms_node, net)
            route_props_selected = self.get_props_from_url(self.ms_node,
                                                            selected_route)
            if 'hb' not in net_props_selected['name'] \
                    and 'subnet' in route_props_selected \
                    and route_props_selected["subnet"] != "0.0.0.0/0":
                selected_network = net
                break
        self.assertNotEqual(None, selected_network)

        return selected_network, selected_route, non_mng_if_urls

    @attr('all', 'non-revert', 'story56', 'story56_tc01')
    def test_01_p_default_route(self):
        """
        @tms_id: litpcds_56_tc01
        @tms_requirements_id: LITPCDS-56
        @tms_title: Default routes added to nodes
        @tms_description: Verify a default route has been added to the nodes
            and default route is configured correctly on the peer-nodes. This
            test now covers litpcds_56_tc02 & litpcds_56_tc03
        @tms_test_steps:
        @step: Find the default route in the model
        @result: The default route found
        @step: check each node has a default route
        @result: each node has only one default
        @step: Check config files for each node
        @result: default route contained in one of the config files
        @step: execute ip route command
        @result: ip route output matches nodes default route
        @step: Check if gateway is pingable
        @result: Gateway is pingable
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        for node_url in self.all_node_urls:
            node_fname = self.get_node_filename_from_url(self.ms_node,
                                                            node_url)
            self.assertTrue(node_fname is not None)
            self.log('info', "Running checks for node {0}".format(node_fname))

            self.log('info', "Get default route")
            route_url = self.get_default_route_url(node_url)
            self.assertTrue(route_url is not None)

            route_props = self.get_props_from_url(self.ms_node, route_url)
            default_gateway = route_props["gateway"]

            self.log('info', "Check if config file exists")
            path = "{0}/route-*".format(const.NETWORK_SCRIPTS_DIR)
            dir_contents = self.list_dir_contents(node_fname, path)
            self.assertNotEqual([], dir_contents)

            self.log('info', "Check route file content")
            std_out = self.get_file_contents(node_fname, path)
            self.log("info", "default_gateway=" + default_gateway)

            has_content = False
            for line in std_out:
                if "{0}".format(default_gateway) in line and "0.0.0.0" in line:
                    has_content = True
            self.assertTrue(has_content)

            self.log('info', "Check route table")
            cmd = self.net.get_route_cmd("-n")
            std_out, _, _ = self.run_command(node_fname, cmd,
                                                        default_asserts=True)

            has_content = False
            for line in std_out:
                if default_gateway in line \
                    and "0.0.0.0" in line \
                        and "UG" in line:
                    has_content = True
            self.assertTrue(has_content)

            self.log('info', "Check if gateway is pingable")
            cmd = self.net.get_ping_cmd(default_gateway, 1)
            _, _, ret_code = self.run_command(node_fname, cmd)
            self.assertEqual(0, ret_code)

    # attr('all', 'non-revert', 'story56', 'story56_tc02')
    def obsolete_02_p_gateway_is_accessible(self):
        """
        Merged with test_01_p_default_route
        #tms_id: litpcds_56_tc02
        #tms_requirements_id: LITPCDS-56
        #tms_title: Gateway is accessible
        #tms_description: Verify the default route on nodes and ms are pingable
        #tms_test_steps:
        #step: Find all the routes in the model
        #result: All the routes in the model found
        #step: For each node and ms execute command on route ips
        #result: Route ips are pingable
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    # attr('all', 'non-revert', 'story56', 'story56_tc03')
    def obsolete_03_p_add_route_ms(self):
        """
        Merged with test_01_p_default_route
        #tms_id: litpcds_56_tc03
        #tms_requirements_id: LITPCDS-56
        #tms_title: Route item configured correctly
        #tms_description: Verify that the route item on ms created in C.I is
            created and configured correctly
        #tms_test_steps:
        #step: on ms execute "/sbin/route -n" command
        #result: /sbin/route -n output is not empty and configured
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'non-revert', 'story56', 'story56_tc04')
    def test_04_p_add_route_node(self):
        """
        @tms_id: litpcds_56_tc04
        @tms_requirements_id: LITPCDS-56
        @tms_title: Non-default route configured correctly on managed nodes
        @tms_description: Verify that non-default routes defined in the
                          model for managed nodes are configured correctly
        @tms_test_steps:
            @step: Find the non-default route
            @result: the non-default route found
            @step: Checks that the non-default route is configured correctly
                   by checking the contents of
                   /etc/sysconfig/network-scripts/route-* and the output of
                   /sbin/route -n
            @result: The non-default route configured as expected.
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """

        _, selected_route, _ = self.select_non_mgmt_route_eth_network()
        subnet = self.get_props_from_url(self.ms_node, selected_route,
                                         filter_prop='subnet').split("/")[0]
        gateway = self.get_props_from_url(self.ms_node, selected_route,
                                          filter_prop='gateway')

        # ITERATE THROUGH ALL NODE URLS
        for node_url in self.node_urls:
            node_fname = self.get_node_filename_from_url(
                self.ms_node, node_url)
            self.assertFalse(node_fname is None)

            path = '{0}/route-*'.format(const.NETWORK_SCRIPTS_DIR)
            self.list_dir_contents(node_fname, path)
            file_contents = self.get_file_contents(node_fname, path)

            has_content = False
            for line in file_contents:
                if gateway in line \
                        and subnet in line:
                    has_content = True
            self.assertTrue(has_content)

            # CHECK ROUTE TABLE
            cmd = self.net.get_route_cmd("-n")
            std_out, _, _ = self.run_command(node_fname, cmd,
                                             default_asserts=True)

            has_content = False
            for line in std_out:
                if gateway in line \
                        and subnet in line \
                        and "UG" in line:
                    has_content = True
            self.assertTrue(has_content)

    def obsolete_05_p_add_overlapping_route(self):
        """
        #tms_id: litpcds_56_tc05
        #tms_requirements_id: LITPCDS-56
        #tms_title: Add overlapping route
        #tms_description: Verify that a overlapping routes can be added
            to the peer-nodes
        #tms_test_steps:
        #step: Create a route with subnet '1.1.1.0/24' and via '10.10.10.1'
        #result: Route created
        #step: Create a route with subnet '1.1.1.0/21' and via '10.10.10.254'
        #result: Route created
        #step: created and run plan
        #result: plan created
        #result: routes configured correctly
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    @attr('all', 'non-revert', 'story56', 'story56_tc06', 'cdb_priority1')
    def test_06_p_update_route_subnet_and_gateway(self):
        """
        @tms_id: litpcds_56_tc06
        @tms_requirements_id: LITPCDS-56
        @tms_title: Update route subnet and gateway
        @tms_description: Verify that route gateway property can be updated
        successfully
        @tms_test_steps:
        @step: Update subnet on "traffic1" item
        @result: Subnet updated
        @step: Update subnet and gateway on "traffic2" item
        @result: Gateway and subnet updated
        @step: Update ipaddresses on node1 and node2 network interface
        @result: Ipaddresses updated
        @step: Create and run plan
        @result: Plan ran successfully
        @step: Ensure route config file was created with correct content
        @result: Route config file created with correct content
        @tms_test_precondition: NA
        @tms_execution_type: Automated
        """
        selected_network, selected_route, non_mng_if_urls = \
            self.select_non_mgmt_route_eth_network()

        self.log('info', "1. Get all device names")
        device_names = []
        for if_url in non_mng_if_urls:
            device_name_prop = self.get_props_from_url(self.ms_node, if_url,
                                                    filter_prop='device_name')
            if device_name_prop is not None:
                device_names.append(device_name_prop)
        self.assertNotEqual([], device_names)

        self.log('info', "2. Backup properties of items to be updated")
        self.backup_path_props(self.ms_node, selected_route)
        self.backup_path_props(self.ms_node, selected_network)
        for url in non_mng_if_urls:
            self.backup_path_props(self.ms_node, url)

        self.log('info', "3. Backup ifcfg file on each node")
        for node in self.peer_nodes:
            for device in device_names:
                ifcfg_file = \
                    "{0}/ifcfg-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                                                device)
                self.backup_file(node, ifcfg_file,
                                 restore_after_plan=True,
                                 assert_backup=False)

        self.log('info', "4. Update network, route and eth")
        props = "subnet='20.20.20.0/24'"
        self.execute_cli_update_cmd(self.ms_node, selected_network, props)

        props = "gateway='20.20.20.254' subnet='22.22.22.0/24'"
        self.execute_cli_update_cmd(self.ms_node, selected_route, props)

        ipaddress = netaddr.IPAddress("20.20.20.78")
        for url in non_mng_if_urls:
            props = "ipaddress=" + str(ipaddress)
            self.execute_cli_update_cmd(self.ms_node, url, props)
            ipaddress += 1

        self.run_and_check_plan(self.ms_node, const.PLAN_COMPLETE, 20)

        self.log('info', "5. Ensure route file contents and route table are "
                        "correct for each peer node")
        for node in self.peer_nodes:
            for device in device_names:
                path = "{0}/route-{1}".format(const.NETWORK_SCRIPTS_DIR,
                                                                    device)
                std_out = self.get_file_contents(node, path)
                has_content = False
                for line in std_out:
                    if "20.20.20.254" in line and '22.22.22.0' in line:
                        has_content = True
                self.assertTrue(has_content)

                cmd = self.net.get_route_cmd("-n")
                std_out, _, _ = self.run_command(node, cmd,
                                                        default_asserts=True)
                has_content = False
                for line in std_out:
                    if "20.20.20.254" in line and '22.22.22.0' in line and \
                            "UG" in line and device in line:
                        has_content = True
                self.assertTrue(has_content)

    #@attr('all', 'non-revert', 'story56', 'story56_tc07')
    def obsolete_07_n_removed_properties(self):
        """
        Covered in AT "validation/invalid_model_scenarios.at" in core
        #tms_id: litpcds_56_tc07
        #tms_requirements_id: LITPCDS-56
        #tms_title: Update with invalid properties
        #tms_description: Update in network item with invalid properties
            results in a PropertyNotAllowedError
        #tms_test_steps:
        #step: Update network type on "/infrasture" path with invalid "gateway"
            and "default_gateway" property
        #result: Error thrown: PropertyNotAllowedError
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    def obsolete_08_n_no_gateway(self):
        """
        Description:
            This test ensures that default route is mandatory (0.0.0.0/0)
            for every server.

        Actions:
            1. remove default gateway item
            2. remove default gateway link
            3. create plan and run validation
            4. validation error is expected

        Result:
            ValidationError: A default route is required for Node
        """
        pass

    def obsolete_09_n_no_default_gateway(self):
        """
        Description:
            This test ensures that default route is mandatory (0.0.0.0/0)
            for every server.

        Actions:
            1. Create a non-default gateway item with the same name property
               what default gateway item has
            2. update default gateway item name property (this breaks link)
            3. create plan and run validation
            4. validation error is expected

        Result:
            ValidationError: A default route is required for Node
        """
        pass

    #@attr('all', 'non-revert', 'story56', 'story56_tc10')
    def obsolete_10_n_multiple_default_gateway(self):
        """
        Converted to AT "test_10_n_multiple_default_gateway.at" in network
        #tms_id: litpcds_56_tc10
        #tms_requirements_id: LITPCDS-56
        #tms_title: Multiple default gateway
        #tms_description: Verify that default route is mandatory (0.0.0.0/0)
            for every server and there is only one mandatory gateway is defined
        #tms_test_steps:
        #step: Create route item in "infrastructure" with property
            subnet='0.0.0.0/0'
        #result: Route created
        #step: Create network item in "infrastructure" with property
            subnet='10.10.10.0/24'
        #result: Network created
        #step: Inherit route onto node1
        #result: Route created on node1
        #step: Create eth item on node1
        #result: Item created
        #step: Inherit route onto node2
        #result: Route created on node2
        #step: Create plan and run plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Destination subnet
            "0.0.0.0/0" is duplicated across several routes.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'non-revert', 'story56', 'story56_tc11')
    def obsolete_11_n_gateway_not_in_network(self):
        """
        Converted to AT "test_11_n_gateway_not_in_network.at" in network
        #tms_id: litpcds_56_tc11
        #tms_requirements_id: LITPCDS-56
        #tms_title: Gateway not in network
        #tms_description: Verify gateway not reachable when invalid gateway
            property set.
        #tms_test_steps:
        #step: Create route item in "infrastructure" with subnet set to
            gateway='gateway='9.9.9.1''
        #result: Route created
        #step: Create network item in "infrastructure"
        #result: Network created
        #step: Inherit route onto node1
        #result: Route created on node1
        #step: Create eth item on node1
        #result: Item created
        #step: Inherit route onto node2
        #result: Route created on node2
        #step: Create eth item on node2
        #result: Item created
        #step: Create plan and run plan
        #result: Error thrown: ValidationError
        #result: Message shown: Route gateway is not reachable from any
            of the interfaces
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'non-revert', 'story56', 'story56_tc12')
    def obsolete_12_n_add_default_route_duplicate_same_gw(self):
        """
        Converted to AT "test_12_n_add_default_route_duplicate_same_gw.at" in
            network
        #tms_id: litpcds_56_tc12
        #tms_requirements_id: LITPCDS-56
        #tms_title: Validate user defined gateway IP
        #tms_description: Verify a user updated gateway IP will throw an error
            when there is a conflict in property values.
        #tms_test_steps:
        #step: Create route item in "infrastructure" with property
            subnet='0.0.0.0/0' and gateway='192.168.0.1'
        #result: Route created
        #step: Create network item in "infrastructure" with property
           subnet='10.10.10.0/24'
        #result: Network created
        #step: Inherit route onto node1
        #result: Route created on node1
        #step: Create eth item on node1
        #result: Item created
        #step: Inherit route onto node2
        #result: Route created on node2
        #step: Create eth item on node2, Create plan and run plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Destination subnet
            "0.0.0.0/0" is duplicated across several routes.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'non-revert', 'story56', 'story56_tc13')
    def obsolete_13_n_add_default_route_duplicate_different_gw(self):
        """
        Converted to AT "test_13_n_add_default_route_duplicate_different_gw.at"
            in network
        #tms_id: litpcds_56_tc13
        #tms_requirements_id: LITPCDS-56
        #tms_title: Validate user defined gateway IP
        #tms_description: Verify a user updated gateway IP will throw an error
            when there is a conflict in property values.
        #tms_test_steps:
        #step: Create route item in "infrastructure" with property
            subnet='0.0.0.0/0' and gateway='10.10.10.1'
        #result: Route created
        #step: Create network item in "infrastructure" with property
            subnet='10.10.10.0/24'
        #result: Network created
        #step: Inherit route onto node1
        #result: Route created on node1
        #step: Create eth item on node1
        #result: Item created
        #step: Inherit route onto node2
        #result: Route created on node2
        #step: Create eth item on node2, create plan and run plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Destination subnet
            "0.0.0.0/0" is duplicated across several routes.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'non-revert', 'story56', 'story56_tc14')
    def obsolete_14_n_add_route_duplicate(self):
        """
        Converted to AT "test_14_n_add_route_duplicate.at" in network
        #tms_id: litpcds_56_tc14
        #tms_requirements_id: LITPCDS-56
        #tms_title: Validate user defined gateway IP
        #tms_description: Verify a user updated gateway IP will throw an error
            when there is a conflict in property values.
        #tms_test_steps:
        #step: Create route item in "infrastructure" with property
            subnet='1.1.1.0/24' and gateway='10.10.10.1'
        #result: Route created
        #step: Create route item in "infrastructure" with property
            subnet='1.1.1.0/24' and gateway='10.10.10.254'
        #result: Route created
        #step: Create network item in "infrastructure" with property
            subnet='10.10.10.0/24'
        #result: Network created
        #step: Create another network item in "infrastructure" with property
            subnet='10.10.10.0/24'
        #result: Network created
        #step: Inherit first route onto node1
        #result: Route created on node1
        #step: Create eth item on node1
        #result: Item created
        #step: Inherit first route onto another node1 item
        #result: Another route created on node1
        #step: Inherit first route onto node2
        #result: route created on node2
        #step: Create eth item on node2, create plan and run plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Destination subnet
            "1.1.1.0/24" is duplicated across several routes.
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    def obsolete_15_n_update_default_route_subnet(self):
        """
        Description:
            This test ensures that user can update gateway IP, and validate
            catch if there is a conflict in default route property values

        Actions:
            1. Update default route subnet property
            2. create plan and run validation
            3. validation error is expected

        Result:
            ValidationError: A default route is required for Node
        """
        pass

    #attr('all', 'non-revert', 'story56', 'story56_tc16')
    def obsolete_16_n_update_route_subnet(self):
        """
        Converted to AT "test_16_n_update_route_subnet.at" in network
        #tms_id: litpcds_56_tc16
        #tms_requirements_id: LITPCDS-56
        #tms_title: Update route subnet
        #tms_description: This test ensures that user can update gateway IP,
            and validate catch if there is a conflict in non-default route
            property values.
        #tms_test_steps:
        #step: Update route item in "infrastructure" with property
            subnet='20.20.20.0/24'
        #result: Route updated
        #step: Update gateway item in "infrastructure"
        #result: Gateway updated
        #step: Update network item on node1 with property
            subnet='20.20.20.78'
        #result: Network item updated
        #step: Update network item on node2 with property
            subnet='20.20.20.78'
        #result: Network item updated
        #step: Execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Route gateway is not
            reachable from any of the interfaces on node
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('all', 'non-revert', 'story56', 'story56_tc17')
    def obsolete_17_n_update_route_subnet_to_default(self):
        """
        Converted to AT "test_17_n_update_route_subnet_to_default.at" in
            network
        #tms_id: litpcds_56_tc17
        #tms_requirements_id: LITPCDS-56
        #tms_title: Update route subnet
        #tms_description: This test ensures that user can update subnet
            property, and validate catches if there is more than one default
            gateway
        #tms_test_steps:
        #step: Update route item in "infrastructure" with property
            subnet='0.0.0.0/0'
        #result: Route updated
        #step: Execute create plan
        #result: Error thrown: ValidationError
        #result: Message shown: Create plan failed: Destination subnet
            0.0.0.0/0 is duplicated across several routes
        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass

    #@attr('pre-reg', 'revert', 'story56', 'story56_tc18')
    def obsolete_18_n_redundant_route(self):
        """
        Description:
            LITPCDS-7422: Disallow new route to a subnet already reachable
            through any interface.

        Actions:
            1. Create a route to already existing network for IPV4
            2. Create a route to already existing network for IPV6
            2. create plan
            3. validation errors are expected

        Result:
            ValidationError for ipv6 and ipv4:
             A route with value "<mgmt subnet>" for property "subnet" is
             invalid as it is accessible via interface named
        """
        pass
