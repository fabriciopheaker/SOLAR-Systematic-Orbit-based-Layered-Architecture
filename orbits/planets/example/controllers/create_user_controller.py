
from flask import g
from orbits.planets.example.controllers.inputs.create_user_input import CreateUserInput
from orbits.planets.example.resources.user_resource import UserResource
from orbits.planets.example.usecases.create_user_usecase import create_user_use_case


class CreateUserController:

    @staticmethod
    def create():
        data = g.solar_data
        user_input = CreateUserInput(data)
        output = create_user_use_case.execute(user_input)
        return UserResource.to_object(output), 201

