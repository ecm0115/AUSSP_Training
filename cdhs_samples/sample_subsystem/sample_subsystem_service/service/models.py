"""
Sample Subsystem Models
Author: Eirik Mulder (ecm0115@auburn.edu)
"""
import graphene


class SystemStatus(graphene.ObjectType):
    """
    ID: 00
    """
    error_detected = graphene.Boolean()
    status_message = graphene.String()
    system_time = graphene.Int()