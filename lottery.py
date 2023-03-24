import smartpy as sp

class Lottery(sp.Contract):
    def __init__(self,_admin):
        self.init(
            players = sp.map(l={}, tkey=sp.TNat, tvalue=sp.TAddress),
            ticket_cost = sp.tez(1),
            tickets_available = sp.nat(4),
            max_tickets = sp.nat(4),
            admin = _admin,
            tickets_sold = sp.nat(0),
        )
    
    @sp.entry_point
    def buy_ticket(self, ticket_buy):
        # Sanity checks
        sp.verify(self.data.tickets_available > 0, "NO TICKETS AVAILABLE")
        sp.verify(sp.amount >= sp.mul(self.data.ticket_cost, ticket_buy), "INVALID AMOUNT")

        # Storage updates

        sp.for var in sp.range(0, ticket_buy, step=1):
            self.data.players[sp.len(self.data.players)] = sp.sender

        #self.data.players[sp.len(self.data.players)] = sp.sender
        #self.data.tickets_available = sp.as_nat(self.data.tickets_available - 1)
        self.data.tickets_available = sp.as_nat(self.data.tickets_available - ticket_buy)
        self.data.tickets_sold = self.data.tickets_sold + ticket_buy

        # Return extra tez balance to the sender
        #extra_balance = sp.amount - self.data.ticket_cost
        extra_balance = sp.amount - (sp.mul(self.data.ticket_cost, ticket_buy))
        sp.if extra_balance > sp.mutez(0):
            sp.send(sp.sender, extra_balance)

    @sp.entry_point
    def end_game(self, random_number):
        sp.set_type(random_number, sp.TNat)

        # Sanity checks
        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORISED")
        sp.verify(self.data.tickets_available == 0, "GAME IS YET TO END")

        # Pick a winner
        winner_id = random_number % self.data.max_tickets
        winner_address = self.data.players[winner_id]

        # Send the reward to the winner
        sp.send(winner_address, sp.balance)

        # Reset the game
        self.data.players = {}
        self.data.tickets_available = self.data.max_tickets
        self.data.tickets_sold = sp.nat(0)

    @sp.entry_point
    def default(self):
        sp.failwith("NOT ALLOWED")

    @sp.entry_point
    def change_cost(self, new_cost):

        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORIZED")
        sp.verify(self.data.tickets_sold == 0, "GAME IS ON")

        self.data.ticket_cost = sp.utils.nat_to_tez(new_cost)

    @sp.entry_point
    def change_max(self, new_max):

        sp.verify(sp.sender == self.data.admin, "NOT_AUTHORIZED")
        sp.verify(self.data.tickets_sold == 0, "GAME IS ON")

        self.data.max_tickets = sp.as_nat(new_max)

@sp.add_test(name = "main")
def test():
    scenario = sp.test_scenario()

    # Test accounts
    admin = sp.test_account("admin")
    alice = sp.test_account("alice")
    bob = sp.test_account("bob")
    mike = sp.test_account("mike")

    # Contract instance
    lottery = Lottery(admin.address)
    scenario += lottery

    # buy_ticket
    scenario.h2("buy_ticket (valid test)")
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(2), sender = alice)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = bob)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = mike)

    scenario.h2("buy_ticket (failure test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(1), sender = alice, valid = False)

    # change_failure_tests
    scenario.h2("change_cost (failure test) - game is on")
    scenario += lottery.change_cost(7).run(sender = admin, valid = False)
    scenario.h2("change_max (failure test)")
    scenario += lottery.change_max(12).run(sender = admin, valid = False)

    # end_game
    scenario.h2("end_game (valid test)")
    scenario += lottery.end_game(21).run(sender = admin)

    # change_failure_tests
    scenario.h2("change_cost (failure test) - non admin")
    scenario += lottery.change_cost(7).run(sender = bob, valid = False)
    scenario.h2("change_max (failure test)")
    scenario += lottery.change_max(12).run(sender = alice, valid = False)


    # change_cost
    scenario.h2("change_cost (valid test)")
    scenario += lottery.change_cost(7).run(sender = admin)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(7), sender = alice)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(14), sender = bob)
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(7), sender = alice)

    scenario.h2("change_cost (failure) test)")
    scenario += lottery.buy_ticket(1).run(amount = sp.tez(3), sender = bob, valid=False)

    # change_max 
    scenario.h2("change_max (valid test)")
    scenario += lottery.end_game(21).run(sender = admin)
    scenario += lottery.change_max(2).run(sender = admin)
    scenario += lottery.buy_ticket(2).run(amount = sp.tez(14), sender = bob)


    
