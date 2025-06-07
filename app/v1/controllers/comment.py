from sqlalchemy import text
from sqlalchemy.orm import Session


def get_base_comment_and_count(post_id: int, session: Session):
    raw_sql = text(
        """
        WITH child_cte AS (
            SELECT 
                parent_comment_id,
                COUNT(*) AS reply_count
            FROM comments
            WHERE parent_comment_id IS NOT NULL
            GROUP BY parent_comment_id
        )
        SELECT 
            base.id,
            base.created_at,
            base.modified_at,
            base.content,
            base.user_id,
            base.post_id,
            base.parent_comment_id,
            COALESCE(child_cte.reply_count, 0) AS reply_count
        FROM comments AS base
        LEFT JOIN child_cte ON base.id = child_cte.parent_comment_id
        WHERE 
            base.parent_comment_id IS NULL 
        AND
            base.post_id = :post_id;
    """
    )

    result = session.execute(raw_sql, {"post_id": post_id})
    comments = result.fetchall()
    return [dict(row._mapping) for row in comments]
