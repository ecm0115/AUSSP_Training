"""
Sample Subsystem Service
Author: Eirik Mulder (ecm0115@auburn.edu)
"""

import graphene
from sample_subsystem_api import SampleHardware
from kubos_service.config import Config
from . import models

service_name = "sample_subsystem_service"
config = Config("sample_subsystem_service")
sample_interface = SampleHardware(config.raw["serial"]["device"], config.raw["serial"]["baudrate"])


####################################
##
##   Mutation Class Definitions  |
##                              V
####################################
class WriteSystemStatus(graphene.Mutation):
    """
    ID: 00
    """

    class Arguments:
        system_message = graphene.Argument(graphene.String, required=True)

    new_status = graphene.Field(models.SystemStatus)
    write_success = graphene.Boolean()

    def mutate(root, info, system_message):
        # Aware that we could use *arguments instead, chose to keep arguments labeled for user readability.

        sample_interface.write_system_status(system_message)

        write_success = True
        new_status = models.StatusWord(
            system_message=sample_interface.read_system_message(),
            error_detected=sample_interface.get_error_detected(),
            system_time=sample_interface.get_time(),
        )
        # Mutations return a copy of themselves with class variables filled out.
        return WriteSystemStatus(new_status=new_status, write_success=write_success)


class Query(graphene.ObjectType):
    system_status = graphene.Field(models.SystemStatus)

    def resolve_system_status(self, info):
        """
        ID: 00
        """
        return models.StatusWord(
            system_message=sample_interface.read_system_message(),
            error_detected=sample_interface.get_error_detected(),
            system_time=sample_interface.get_time(),
        )


class Mutation(graphene.ObjectType):
    write_system_status = WriteSystemStatus.Field()


schema = graphene.Schema(query=Query, mutation=Mutation, auto_camelcase=False)
