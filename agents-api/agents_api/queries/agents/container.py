from dependency_injector import containers, providers

from .create_agent import CreateAgentQuery


class AgentsQueriesContainer(containers.DeclarativeContainer):
    db_pool = providers.Resource()
    config = providers.Configuration()

    create = providers.Factory(
        CreateAgentQuery,
        db_pool=db_pool,
    )
