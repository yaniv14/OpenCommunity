"""
This file demonstrates writing tests using the unittest module. These will pass
when you run "manage.py test".

Replace this with more appropriate tests for your application.
"""

from django.test import TestCase
from communities.models import Community
from users.models import OCUser
from issues.models import Issue
from issues.shultze_vote import user_vote
from shultze.models import IssuesGraph, IssueEdge

class GraphToResults(TestCase):
    def setUp(self):
        self.com = Community.objects.create(name='com1')
        self.usr = OCUser.objects.create_user('a@b.com')
        self.graph = IssuesGraph.objects.create(community=self.com)

    def test_simple_example(self):
        """Check basic logic from graph to Schulze NPR"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)

        #update weights on graph's edges
        edge = IssueEdge.objects.get(graph=graph, from_node=issue_a, to_node=issue_b)
        edge.weight = 8
        edge.save()
        edge = IssueEdge.objects.get(graph=graph, from_node=issue_b, to_node=issue_a)
        edge.weight = 3
        edge.save()
        edge = IssueEdge.objects.get(graph=graph, from_node=issue_a, to_node=issue_c)
        edge.weight = 3
        edge.save()
        edge = IssueEdge.objects.get(graph=graph, from_node=issue_c, to_node=issue_a)
        edge.weight = 4
        edge.save()
        edge = IssueEdge.objects.get(graph=graph, from_node=issue_b, to_node=issue_c)
        edge.weight = 6
        edge.save()
        edge = IssueEdge.objects.get(graph=graph, from_node=issue_c, to_node=issue_b)
        edge.weight = 3
        edge.save()
        
        #calculate results
        output = graph.get_schulze_npr_results()

        # Run tests
        self.assertEqual(output, {
            'candidates': set([issue_a.id, issue_b.id, issue_c.id]),
            'rounds': [{'winner': issue_a.id}, {'winner': issue_b.id}, {'winner': issue_c.id}],
            'order': [issue_a.id, issue_b.id, issue_c.id]
        })


class BallotsIO(TestCase):
    def setUp(self):
        self.com = Community.objects.create(name='com1')
        self.usr = OCUser.objects.create_user('a@b.com')
        self.graph = IssuesGraph.objects.create(community=self.com)
    
    def test_vote_reversal(self):
        """Check voting reversibility"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        issue_d = Issue.objects.create(community=com, created_by=usr, title='issue_d')
        issue_e = Issue.objects.create(community=com, created_by=usr, title='issue_e')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)
        graph.add_node(issue_d)
        graph.add_node(issue_e)

        # Generate data
        input = [
            {"count":1, "ballot":[[issue_a.id], [issue_b.id], [issue_c.id], [issue_d.id], [issue_e.id]]},
        ]
        input_prev = [
            {"count":1, "ballot":[[issue_a.id], [issue_b.id], [issue_c.id], [issue_d.id], [issue_e.id]]},
        ]
        
        # add ballots to graph
        user_vote(com,input,input_prev)
        
        #calculate results
        output = graph.get_edges_dict()

        # Run tests
        self.assertEqual(output, {(1, 2): 0,
            (1, 3): 0,
            (1, 4): 0,
            (1, 5): 0,
            (2, 1): 0,
            (2, 3): 0,
            (2, 4): 0,
            (2, 5): 0,
            (3, 1): 0,
            (3, 2): 0,
            (3, 4): 0,
            (3, 5): 0,
            (4, 1): 0,
            (4, 2): 0,
            (4, 3): 0,
            (4, 5): 0,
            (5, 1): 0,
            (5, 2): 0,
            (5, 3): 0,
            (5, 4): 0}
        )


class BallotsToResults(TestCase):
    def setUp(self):
        self.com = Community.objects.create(name='com1')
        self.usr = OCUser.objects.create_user('a@b.com')
        self.graph = IssuesGraph.objects.create(community=self.com)

    def test_single_voter(self):
        """Check basic logic from ballot to Schulze NPR"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        issue_d = Issue.objects.create(community=com, created_by=usr, title='issue_d')
        issue_e = Issue.objects.create(community=com, created_by=usr, title='issue_e')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)
        graph.add_node(issue_d)
        graph.add_node(issue_e)

        # Generate data
        input = [
            {"count":1, "ballot":[[issue_a.id], [issue_b.id], [issue_c.id], [issue_d.id], [issue_e.id]]},
        ]
        # add ballots to graph
        graph.add_ballots(input)
        
        #calculate results
        output = graph.get_schulze_npr_results()

        # Run tests
        self.assertEqual(output, {
            'order': [issue_a.id, issue_b.id, issue_c.id, issue_d.id, issue_e.id],
            'candidates': set([issue_a.id, issue_b.id, issue_c.id, issue_d.id, issue_e.id]),
            'rounds': [
                {'winner': issue_a.id},
                {'winner': issue_b.id},
                {'winner': issue_c.id},
                {'winner': issue_d.id},
                {'winner': issue_e.id}
            ]
        })

    def test_nonproportionality(self):
        """Check nonproportionality case from ballot to Schulze NPR"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        issue_d = Issue.objects.create(community=com, created_by=usr, title='issue_d')
        issue_e = Issue.objects.create(community=com, created_by=usr, title='issue_e')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)
        graph.add_node(issue_d)
        graph.add_node(issue_e)

        # Generate data
        input = [
            {"count":2, "ballot":[[issue_a.id], [issue_b.id], [issue_c.id], [issue_d.id], [issue_e.id]]},
            {"count":1, "ballot":[[issue_e.id], [issue_d.id], [issue_c.id], [issue_b.id], [issue_a.id]]},
        ]
        # add ballots to graph
        graph.add_ballots(input)
        
        #calculate results
        output = graph.get_schulze_npr_results()

        # Run tests
        self.assertEqual(output, {
            'order': [issue_a.id, issue_b.id, issue_c.id, issue_d.id, issue_e.id],
            'candidates': set([issue_a.id, issue_b.id, issue_c.id, issue_d.id, issue_e.id]),
            'rounds': [
                {'winner': issue_a.id},
                {'winner': issue_b.id},
                {'winner': issue_c.id},
                {'winner': issue_d.id},
                {'winner': issue_e.id}
            ]
        })


class Itamar(TestCase):
    def setUp(self):
        self.com = Community.objects.create(name='com1')
        self.usr = OCUser.objects.create_user('a@b.com')
        self.graph = IssuesGraph.objects.create(community=self.com)
    
    def test_results(self):
        """Check results for Itamar's example"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        issue_d = Issue.objects.create(community=com, created_by=usr, title='issue_d')
        issue_e = Issue.objects.create(community=com, created_by=usr, title='issue_e')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)
        graph.add_node(issue_d)
        graph.add_node(issue_e)
        
        # Generate data
        input=[
            {'count': 1, 'ballot': [[issue_b.id, issue_c.id, issue_d.id, issue_e.id], [issue_a.id]]},
            {'count': 1, 'ballot': [[issue_d.id], [issue_a.id, issue_b.id, issue_c.id, issue_e.id]]},
            {'count': 1, 'ballot': [[issue_a.id], [issue_b.id, issue_c.id, issue_d.id, issue_e.id]]},
        ]
        
        # add ballots to graph
        user_vote(com,input)

        #calculate results
        output = graph.get_schulze_npr_results(tie_breaker = [1, 2, 3, 5])
        # Run tests
        self.assertEqual(output,
                        {'tie_breaker': [1, 2, 3, 5], 
                        'candidates': set([1, 2, 3, 4, 5]), 
                        'order': [4, 1, 2, 3, 5], 
                        'rounds': [{'winner': 4}, 
                            {'winner': 1, 'tied_winners': set([1, 2, 3, 5])}, 
                            {'winner': 2, 'tied_winners': set([2, 3, 5])}, 
                            {'winner': 3, 'tied_winners': set([3, 5])}, 
                            {'winner': 5}]}
        )

class RatedOrders(TestCase):
    def setUp(self):
        self.com = Community.objects.create(name='com1')
        self.usr = OCUser.objects.create_user('a@b.com')
        self.graph = IssuesGraph.objects.create(community=self.com)

    def test_results(self):
        """Check order rating"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        issue_d = Issue.objects.create(community=com, created_by=usr, title='issue_d')
        issue_e = Issue.objects.create(community=com, created_by=usr, title='issue_e')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)
        graph.add_node(issue_d)
        graph.add_node(issue_e)
        
        # Generate data
        input=[
            {'count': 1, 'ballot': [[issue_b.id, issue_c.id, issue_d.id, issue_e.id], [issue_a.id]]},
            {'count': 1, 'ballot': [[issue_d.id], [issue_a.id, issue_b.id, issue_c.id, issue_e.id]]},
            {'count': 1, 'ballot': [[issue_a.id], [issue_b.id, issue_c.id, issue_d.id, issue_e.id]]},
        ]
        
        # add ballots to graph
        user_vote(com,input)

        #calculate results
        output = graph.get_schulze_npr_order_and_rating(tie_breaker=[1, 2, 3, 5])
        # Run tests
        self.assertEqual(output,
                        [{(4, 1): 1},
                         {(1, 2): 0},
                         {(2, 3): 0},
                         {(3, 5): 0}]
        )

    def test_results_sum_and_normalization(self):
        """Check order rating after bottom->up sum and normalization"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)
        
        # Generate data
        input=[
            {'count': 5, 'ballot': [[issue_a.id],[issue_b.id], [issue_c.id]]},
        ]
        
        # add ballots to graph
        user_vote(com,input)

        #calculate results
        output = graph.get_schulze_npr_order_and_rating_bottom_up_sum()
        # Run tests
        self.assertEqual(output,
                        [{1: 10},
                         {2: 5},
                         {3: 0}]
        )

    def test_results_sum_and_normalization(self):
        """Check new normalization"""
        
        com = self.com
        usr = self.usr
        graph = self.graph
        
        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')
        
        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)
        
        # Generate data
        input=[
            {'count': 5, 'ballot': [[issue_a.id],[issue_b.id], [issue_c.id]]},
        ]
        
        # add ballots to graph
        user_vote(com,input)

        #calculate results
        output = graph.get_schulze_npr_order_and_rating_bottom_up_sum()
        # Run tests
        normalized_output = graph.normalize_ordered_rating_bottom_up_sum(output, 2, 5)
        self.assertEqual(normalized_output,
                        [{1: 5},
                         {2: 3},
                         {3: 2}]
        )

    def test_results_sum_and_normalization_single_voter(self):
        """Check normalization with a single voter usecase"""

        com = self.com
        usr = self.usr
        graph = self.graph

        #create issues
        issue_a = Issue.objects.create(community=com, created_by=usr, title='issue_a')
        issue_b = Issue.objects.create(community=com, created_by=usr, title='issue_b')
        issue_c = Issue.objects.create(community=com, created_by=usr, title='issue_c')

        #add issues as graph nodes
        graph.add_node(issue_a)
        graph.add_node(issue_b)
        graph.add_node(issue_c)

        # Generate data
        input=[
            {'count': 1, 'ballot': [[issue_a.id],[issue_b.id], [issue_c.id]]},
            ]

        # add ballots to graph
        user_vote(com,input)

        #calculate results
        output = graph.get_schulze_npr_order_and_rating_bottom_up_sum()
        # Run tests
        normalized_output = graph.normalize_ordered_rating_bottom_up_sum(output, 0, 1)
        self.assertEqual(normalized_output,
            [{1: 1},
             {2: 1},
             {3: 0}]
        )