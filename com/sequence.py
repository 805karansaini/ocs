from com.variables import *


# Creating class for sequence objects
class Sequence(object):
    # Defining constructor -
    def __init__(
        self,
        sequence_id=None,
        sequence_type=None,
        ladder_id=None,
        action=None,
        order_type=None,
        quantity=None,
        price=None,
        order_time=None,
        order_sent_time=None,
        last_update_time=None,
        filled_quantity=None,
        status=None,
        percentage=None,
    ):
        # Setting attributes for sequence object
        self.sequence_id = sequence_id
        self.sequence_type = sequence_type
        self.ladder_id = ladder_id
        self.action = action
        self.order_type = order_type
        self.quantity = quantity
        self.price = price
        self.order_time = order_time
        self.order_sent_time = order_sent_time
        self.last_update_time = last_update_time
        self.filled_quantity = filled_quantity
        self.status = status
        self.percentage = percentage

    # Get all attributes of sequence object
    def __str__(self):
        return f"Sequence(sequence_id={self.sequence_id}, sequence_type={self.sequence_type}, ladder_id={self.ladder_id}, action={self.action}, order_type={self.order_type},\
                quantity={self.quantity}, price={self.price}, order_time={self.order_time}, order_sent_time={self.order_sent_time}), \
                last_update_time={self.last_update_time}, filled_quantity={self.filled_quantity}, status={self.status}, percentage={self.percentage})"

    # Get all atributes in list format
    def get_list_of_sequence_values(self):
        return [
            self.sequence_id,
            self.sequence_type,
            self.ladder_id,
            self.action,
            self.order_type,
            self.quantity,
            self.price,
            self.order_time,
            self.order_sent_time,
            self.last_update_time,
            self.filled_quantity,
            self.status,
            self.percentage,
        ]
