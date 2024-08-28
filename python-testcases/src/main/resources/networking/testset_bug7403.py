'''
COPYRIGHT Ericsson 2019
The copyright to the computer program(s) herein is the property of
Ericsson Inc. The programs may be used and/or copied only with written
permission from Ericsson Inc. or in accordance with the terms and
conditions stipulated in the agreement/contract under which the
program(s) have been supplied.

@since:     March 2017
@author:    Paul Chambers
@summary:   Integration
            Agile: STORY-7403
'''

from litp_generic_test import GenericTest
from networking_utils import NetworkingUtils
from litp_cli_utils import CLIUtils
import test_constants
from xml_utils import XMLUtils


class Story7403(GenericTest):
    """
    As a Network Administrator I want Network routes to be modeled
    independently from IP ranges so that I can configure multiple local
    and remote networks without routing conflicts.
    """

    test_ms_if1 = None
    test_node_if1 = None
    test_node_if2 = None

    def setUp(self):
        """
        Description:
            Runs before every single test
        Actions:
            1. Call the super class setup method
            2. Set up variables used in the tests
        Results:
            The super class prints out diagnostics and variables
            common to all tests are available
        """

        # 1. Call super class setup
        super(Story7403, self).setUp()

        # 2. Set up variables used in the test
        self.ms_node = self.get_management_node_filename()
        self.ms_ip = None
        self.all_nodes = None
        self.just_nodes = None
        self.xml = XMLUtils()
        self.cli = CLIUtils()

    def setup_assertions(self):
        """
        Description:
            This method defines certain required variables and
            asserts that their values are correct
        """
        # get MS ip address
        self.ms_ip = self.get_node_att(self.ms_node, 'ipv4')
        self.assertNotEqual("", self.ms_ip)

        # get master server ip address
        self.net = NetworkingUtils()
        self.all_nodes = self.get_managed_node_filenames() + [self.ms_node]
        self.just_nodes = self.get_managed_node_filenames()

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
        super(Story7403, self).tearDown()

        free_nics = \
            self.verify_backup_free_nics(self.ms_node, "/ms")
        self.test_ms_if1 = free_nics[0]
        node_urls = \
            self.find(self.ms_node, "/deployments", "node")
        free_nics = \
            self.verify_backup_free_nics(self.ms_node, node_urls[0],
                                         backup_files=False)
        self.test_node_if1 = free_nics[0]

        # DECONFIGURE test interface
        cmd = "/sbin/ifdown {0}".format(self.test_ms_if1["NAME"])
        self.run_command(self.ms_node, cmd, su_root=True)

        node_urls = self.find(self.ms_node, "/deployments", "node")

        # CLEAN UP ON MS AND NODES
        for node_url in node_urls + ["/ms"]:
            node_fname = self.get_node_filename_from_url(self.ms_node,
                                                         node_url)
            # DELETE ROUTE FILE
            cmd = "/bin/rm -f {0}/route-{1}".\
                format(test_constants.NETWORK_SCRIPTS_DIR,
                       self.test_node_if1["NAME"])

            # DECONFIGURE test interface
            cmd = "/sbin/ifdown {0}".format(self.test_node_if1["NAME"])
            self.run_command(node_fname, cmd, su_root=True)
            # may need to run a restorre snapshot as a workaround

    def get_route_path(self):
        """
        Finds the url of a toute on the ms.
        Returns the url of the route, the routes subnet and gateway.
        """

        ms_route = self.find(self.ms_node, "/infrastructure",
                             "route")[0]
        route_props = self.get_props_from_url(self.ms_node, ms_route)
        subnet, _ = route_props["subnet"].split("/")
        gateway = route_props["gateway"]

        return ms_route, subnet, gateway

    # @attr('pre-reg', 'non-revert', 'story7403', 'story7403_tc1')
    def obsolete_01_p_add_existing_nic_to_bond_check_routing_config(self):
        """
        #Obsoleted as test had tag pre-reg so was not included in KGB
        #tms_id: litpcds_7403_tc01
        #tms_requirements_id: LITPCDS-2069
        #tms_title: add_existing_nic_to_bond_check_routing_config
        #tms_description:
            Add an existing network interface to a newly created bond and
            check the routing table, configuration file and task list
            No route tasks are performed. Ticket was raised, see:
            LITPCDS-7403 Plan has no task to update route when I add an
            existing nic interface to a bond
        #tms_test_steps:
            #step: Collect node and interface urls
            #result: node urls and node interface urls are made known
            #step: Delete the ipaddress and network name of node interface
            #result: Properties are deleted
            #step: Create a master bond on the node interface
            #result: The nodes mater property is set to bond1
            #step: Create a bond with ipaddress, device name and network
            name properties
            #result: A bond with ipaddress, device name and network
            name properties is created
            #step: The nodes route table is checked
            #result: The content of the nodes route table is checked
            #step: Create and run a litp plan
            #result: A plan is created and run.
            #step: The nodes route table is checked once the plan has
            completed
            #result: The changes in the nodes route table is checked
            #step: Check for the creation of the bond ifcfg file on the node
            #result: The correct ifcfg file has been created on the node

        #tms_test_precondition: NA
        #tms_execution_type: Automated
        """
        pass
