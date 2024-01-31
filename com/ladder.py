from com.variables import *

# Class for ladder objects -  ask karan about structure of sequences attribute & entry order filled & exit order filled
class Ladder(object):

    # Defining constructor
    def __init__(
        self,
        ladder_id=None,
        unique_id=None,
        action=None,
        order_type=None,
        total_quantity=None,
        initial_quantity=None,
        subsequent_quantity=None,
        number_of_buckets=None,
        initial_entry_price=None,
        delta_price=None,
        price_movement=None,
        take_profit_buffer=None,
        take_profit_behaviour=None,
        entry_quantity_filled=None,
        exit_quantity_filled=None,
        status=None,
        account_id=None,
        bypass_rm_check=None,
        execution_engine=None,
        sequence_obj_list=None,
    ):

        # Setting attributes for ladder object
        self.ladder_id = int(ladder_id)
        self.unique_id = int(unique_id)
        self.action = action
        self.order_type = order_type
        self.total_quantity = total_quantity
        self.initial_quantity = initial_quantity
        self.subsequent_quantity = subsequent_quantity
        self.number_of_buckets = number_of_buckets
        self.initial_entry_price = initial_entry_price
        self.delta_price = delta_price
        self.price_movement = price_movement
        self.take_profit_buffer = take_profit_buffer
        self.take_profit_behaviour = take_profit_behaviour
        self.entry_quantity_filled = entry_quantity_filled
        self.exit_quantity_filled = exit_quantity_filled
        self.status = status
        self.account_id = account_id
        self.bypass_rm_check = bypass_rm_check
        self.execution_engine = execution_engine

        # Initialize lists to store sequence in 2 parts - 'entry' and 'exit'
        self.entry_sequences = []
        self.exit_sequences = []

        # Check if sequence object is not None
        if sequence_obj_list != None:

            # Iterating sequence objects
            for sequence_obj in sequence_obj_list:

                # Checking if sequence type of sequence object is entry or exit
                if sequence_obj.sequence_type == "Entry":

                    # Appending entry sequence objects to list for entry sequences
                    self.entry_sequences.append(sequence_obj)

                elif sequence_obj.sequence_type == "Exit":

                    # Appending exit sequence objects to list for exit sequences
                    self.exit_sequences.append(sequence_obj)

                else:

                    # Print to console
                    if variables.flag_debug_mode:

                        print(
                            f"Ladder ID = {ladder_id}, Wrong Value for sequence type (Entry/Exit) {sequence_obj.sequence_type=}"
                        )

    # Get all attributes of ladder object
    def _str_(self):

        # Getting all sequences in string format
        entry_sequences_str = "\n\t".join(
            [str(sequence) for sequence in self.entry_sequences]
        )
        exit_sequences_str = "\n\t".join(
            [str(sequence) for sequence in self.exit_sequences]
        )

        return f"Ladder(ladder ID={self.ladder_id},unique_id={self.unique_id}, action={self.action}, order_type={self.order_type}, total_quantity={self.total_quantity}, \
                initial_quantity={self.initial_quantity}, subsequent_quantity={self.subsequent_quantity}, number_of_buckets={self.number_of_buckets}, \
                initial_entry_price={self.initial_entry_price}, delta_price={self.delta_price}, price_movement={self.price_movement}, take_profit_buffer={self.take_profit_buffer}, \
                take_profit_behaviour={self.take_profit_behaviour} entry_oder_filled={self.entry_oder_filled}, exit_oder_filled={self.exit_oder_filled}, status={self.status}\
                \nEntry Sequences:\n\t{entry_sequences_str}\nExit Sequences LEGS:\n\t{exit_sequences_str}\n, Account ID:\n\t{self.account_id}, Bypass RM Check:\n\t{self.bypass_rm_check} )"

    # Get sequence object
    def get_sequence_obj(self, sequence_id):

        # Searching sequence obj in entry sequences
        for sequence_obj in self.entry_sequences:

            if sequence_obj.sequence_id == sequence_id:

                return sequence_obj

        # Searching sequence obj in exit sequences
        for sequence_obj in self.exit_sequences:

            if sequence_obj.sequence_id == sequence_id:

                return sequence_obj
