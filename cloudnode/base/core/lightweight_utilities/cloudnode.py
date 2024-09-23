import os


def create_programmatic_directory(directory, tags=None):
    """Builds programmatic directory for organized storage across cloudnode use cases"""
    # NOTE: /{index}/{tag1}/{value1}/{tag2}/{value2}/swift.{cls_name}/ and swift.{index}.{cls_name}.{id}.json"""
    # NOTE: as of 09/2024 this routine no longer sorts and depends on upstream to organize the tags order
    if tags is not None:
        for tag, value in tags.items(): directory = os.path.join(directory, f"{tag}/{value}/")
    return directory