"""
A fronteira de entrada do Planet example.

O que mora aqui é o que CONTROLAR a passagem: quem pode entrar, o
que precisa chegar e como o dado chega. Nada de negócio.

    request → atmosphere/  → Controller → UseCase → ...

A Atmosphere roda ANTES do Controller, e o Controller recebe a
requisição já tratada.
"""
