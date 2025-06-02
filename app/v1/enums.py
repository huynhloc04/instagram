from enum import Enum


class PostStatus(str, Enum):
    draft = 'draft'
    public = 'public'


class ImageCronEnum(str, Enum):
    used = "used"
    unused = "unused"
