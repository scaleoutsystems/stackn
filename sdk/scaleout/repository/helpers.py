from scaleout.repository.miniorepository import MINIORepository


def get_repository(config=None):
    return MINIORepository(config)
