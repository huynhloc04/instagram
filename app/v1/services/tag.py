#   References: https://iamyogesh.medium.com/what-is-the-best-approach-to-store-hashtags-in-a-database-caa796d714d4

import re

from sqlalchemy.orm import Session

from app.v1.models import Tag, PostTag, Post


def extract_tags(caption: str) -> list[str]:
    """
    Extracts hashtags from a caption.

    Args:
        caption (str): The text of the post caption.

    Returns:
        List[str]: A list of extracted hashtags without the '#' symbol.
    """
    if not caption:
        return []

    # Regular expression to match hashtags (e.g. #sunset, #hello_world)
    return re.findall(r"#(\w+)", caption)


def create_tags(post: Post, session: Session):
    """
    1. Extract tags from post's caption
    2. Save tags to database
    3. Attach tags to post
    """
    extracted_tags = extract_tags(caption=post.caption)
    #   Fetch all existing tags
    existing_tags = session.query(Tag).where(Tag.tag_name.in_(extracted_tags)).all()
    existing_tag_names = {existing_tag.tag_name for existing_tag in existing_tags}
    #   Determine tags to create newly
    new_tag_names = set(extracted_tags) - existing_tag_names

    try:
        tags = [Tag(tag_name=tag_name) for tag_name in new_tag_names]
        session.add_all(tags)
        session.flush()
    except Exception as error:
        raise ValueError(f"Tags created error: {error}")

    try:
        tag_to_post = [*tags, *existing_tags]
        post_tags = [PostTag(tag_id=tag.id, post_id=post.id) for tag in tag_to_post]
        session.add_all(post_tags)
        session.flush()
    except Exception as error:
        raise ValueError(f"Attached tag to post {post.id} error: {error}")
