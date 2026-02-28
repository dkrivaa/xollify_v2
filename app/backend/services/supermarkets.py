from common.core.super_class import SupermarketChain


def get_chain_from_code(chain_code):
    """ Get chain object from chain code """
    # List of all registered supermarket chains
    chains = SupermarketChain.registry
    # Get chain matching given chain code
    chain = next(c for c in chains if c.chain_code == chain_code)

    return chain