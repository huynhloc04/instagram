"""
Search routes for Instagram backend using Elasticsearch.

This module provides API endpoints for:
- User search and auto-completion
- Post content search
- Hashtag discovery and trending
- Advanced search functionality
"""

from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from app.v1.elasticsearch.search import search_service
from app.v1.elasticsearch.indexing import indexing_service
from app.core.extensions import limiter

# Create search blueprint
searchRoute = Blueprint("search", __name__, url_prefix="/search")


@searchRoute.route("/users", methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def search_users():
    """
    Search for users by username, fullname, or bio content.
    
    Query Parameters:
        q (str): Search query
        limit (int): Maximum results (default: 20, max: 50)
        offset (int): Pagination offset (default: 0)
        verified_only (bool): Return only verified users (default: false)
    
    Returns:
        JSON response with user search results
    """
    try:
        # Get query parameters
        query = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 20)), 50)  # Max 50 results
        offset = int(request.args.get("offset", 0))
        verified_only = request.args.get("verified_only", "false").lower() == "true"
        
        if not query:
            return jsonify({
                "success": False,
                "message": "Search query is required"
            }), 400
        
        # Perform search
        results = search_service.search_users(
            query=query,
            limit=limit,
            offset=offset,
            verified_only=verified_only
        )
        
        return jsonify({
            "success": True,
            "data": {
                "users": results["users"],
                "pagination": {
                    "total": results["total"],
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < results["total"]
                }
            },
            "meta": {
                "took": results["took"],
                "max_score": results["max_score"]
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Search failed"
        }), 500


@searchRoute.route("/posts", methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def search_posts():
    """
    Search for posts by caption content, hashtags, or user.
    
    Query Parameters:
        q (str): Search query for caption content
        hashtags (str): Comma-separated hashtags (with or without #)
        user_id (int): Filter posts by specific user ID
        limit (int): Maximum results (default: 20, max: 50)
        offset (int): Pagination offset (default: 0)
        sort_by (str): Sort field (created_at, likes_count, comments_count, relevance)
        sort_order (str): Sort order (asc, desc)
    
    Returns:
        JSON response with post search results
    """
    try:
        # Get query parameters
        query = request.args.get("q", "").strip()
        hashtags_param = request.args.get("hashtags", "").strip()
        user_id = request.args.get("user_id")
        limit = min(int(request.args.get("limit", 20)), 50)  # Max 50 results
        offset = int(request.args.get("offset", 0))
        sort_by = request.args.get("sort_by", "created_at")
        sort_order = request.args.get("sort_order", "desc")
        
        # Parse hashtags
        hashtags = []
        if hashtags_param:
            hashtags = [tag.strip().lstrip("#") for tag in hashtags_param.split(",") if tag.strip()]
        
        # Validate sort parameters
        valid_sort_fields = ["created_at", "likes_count", "comments_count", "relevance"]
        if sort_by not in valid_sort_fields:
            sort_by = "created_at"
        
        if sort_order not in ["asc", "desc"]:
            sort_order = "desc"
        
        # Convert user_id to int if provided
        if user_id:
            try:
                user_id = int(user_id)
            except ValueError:
                return jsonify({
                    "success": False,
                    "message": "Invalid user_id parameter"
                }), 400
        
        # Require at least one search criteria
        if not query and not hashtags and not user_id:
            return jsonify({
                "success": False,
                "message": "At least one search criteria is required (q, hashtags, or user_id)"
            }), 400
        
        # Perform search
        results = search_service.search_posts(
            query=query,
            hashtags=hashtags,
            user_id=user_id,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
            sort_order=sort_order
        )
        
        return jsonify({
            "success": True,
            "data": {
                "posts": results["posts"],
                "pagination": {
                    "total": results["total"],
                    "limit": limit,
                    "offset": offset,
                    "has_more": offset + limit < results["total"]
                }
            },
            "meta": {
                "took": results["took"],
                "max_score": results["max_score"],
                "sort_by": sort_by,
                "sort_order": sort_order
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Search failed"
        }), 500


@searchRoute.route("/hashtags", methods=["GET"])
@limiter.limit("30 per minute")
@jwt_required()
def search_hashtags():
    """
    Search and discover hashtags.
    
    Query Parameters:
        q (str): Search query for hashtag (optional for trending)
        limit (int): Maximum results (default: 20, max: 50)
        trending_only (bool): Return only trending hashtags (default: false)
    
    Returns:
        JSON response with hashtag search results
    """
    try:
        # Get query parameters
        query = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 20)), 50)  # Max 50 results
        trending_only = request.args.get("trending_only", "false").lower() == "true"
        
        # Perform search
        results = search_service.search_hashtags(
            query=query,
            limit=limit,
            trending_only=trending_only
        )
        
        return jsonify({
            "success": True,
            "data": {
                "hashtags": results["hashtags"],
                "total": results["total"]
            },
            "meta": {
                "took": results["took"],
                "trending_only": trending_only
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Search failed"
        }), 500


@searchRoute.route("/autocomplete/users", methods=["GET"])
@limiter.limit("60 per minute")
@jwt_required()
def autocomplete_users():
    """
    Get user auto-completion suggestions.
    
    Query Parameters:
        q (str): Partial query string
        limit (int): Maximum suggestions (default: 10, max: 20)
    
    Returns:
        JSON response with user suggestions
    """
    try:
        # Get query parameters
        query = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 10)), 20)  # Max 20 suggestions
        
        if not query or len(query) < 2:
            return jsonify({
                "success": False,
                "message": "Query must be at least 2 characters long"
            }), 400
        
        # Get suggestions
        suggestions = search_service.autocomplete_users(query, limit)
        
        return jsonify({
            "success": True,
            "data": {
                "suggestions": suggestions
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Autocomplete failed"
        }), 500


@searchRoute.route("/autocomplete/hashtags", methods=["GET"])
@limiter.limit("60 per minute")
@jwt_required()
def autocomplete_hashtags():
    """
    Get hashtag auto-completion suggestions.
    
    Query Parameters:
        q (str): Partial hashtag query
        limit (int): Maximum suggestions (default: 10, max: 20)
    
    Returns:
        JSON response with hashtag suggestions
    """
    try:
        # Get query parameters
        query = request.args.get("q", "").strip()
        limit = min(int(request.args.get("limit", 10)), 20)  # Max 20 suggestions
        
        if not query or len(query) < 1:
            return jsonify({
                "success": False,
                "message": "Query is required"
            }), 400
        
        # Get suggestions
        suggestions = search_service.autocomplete_hashtags(query, limit)
        
        return jsonify({
            "success": True,
            "data": {
                "suggestions": suggestions
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Autocomplete failed"
        }), 500


@searchRoute.route("/trending/hashtags", methods=["GET"])
@limiter.limit("20 per minute")
@jwt_required()
def trending_hashtags():
    """
    Get trending hashtags.
    
    Query Parameters:
        limit (int): Maximum results (default: 20, max: 50)
    
    Returns:
        JSON response with trending hashtags
    """
    try:
        # Get query parameters
        limit = min(int(request.args.get("limit", 20)), 50)  # Max 50 results
        
        # Get trending hashtags
        trending = search_service.get_trending_hashtags(limit)
        
        return jsonify({
            "success": True,
            "data": {
                "hashtags": trending
            }
        }), 200
        
    except ValueError as e:
        return jsonify({
            "success": False,
            "message": f"Invalid parameter: {str(e)}"
        }), 400
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Failed to get trending hashtags"
        }), 500


# Admin routes for index management
@searchRoute.route("/admin/reindex/users", methods=["POST"])
@limiter.limit("2 per hour")
@jwt_required()
def reindex_users():
    """
    Admin endpoint to reindex all users.
    
    Body Parameters:
        limit (int): Batch size (default: 1000)
        offset (int): Starting offset (default: 0)
    
    Returns:
        JSON response with reindexing results
    """
    try:
        # This should have proper admin authentication in production
        # For now, just requiring JWT token
        
        data = request.get_json() or {}
        limit = data.get("limit", 1000)
        offset = data.get("offset", 0)
        
        # Perform bulk indexing
        results = indexing_service.bulk_index_users(limit=limit, offset=offset)
        
        return jsonify({
            "success": True,
            "data": results
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Reindexing failed"
        }), 500


@searchRoute.route("/admin/reindex/posts", methods=["POST"])
@limiter.limit("2 per hour")
@jwt_required()
def reindex_posts():
    """
    Admin endpoint to reindex all posts.
    
    Body Parameters:
        limit (int): Batch size (default: 1000)
        offset (int): Starting offset (default: 0)
    
    Returns:
        JSON response with reindexing results
    """
    try:
        # This should have proper admin authentication in production
        # For now, just requiring JWT token
        
        data = request.get_json() or {}
        limit = data.get("limit", 1000)
        offset = data.get("offset", 0)
        
        # Perform bulk indexing
        results = indexing_service.bulk_index_posts(limit=limit, offset=offset)
        
        return jsonify({
            "success": True,
            "data": results
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Reindexing failed"
        }), 500


@searchRoute.route("/admin/health", methods=["GET"])
@limiter.limit("10 per minute")
@jwt_required()
def elasticsearch_health():
    """
    Check Elasticsearch cluster health.
    
    Returns:
        JSON response with cluster health information
    """
    try:
        from app.core.elasticsearch import es_manager
        
        health = es_manager.health_check()
        
        return jsonify({
            "success": True,
            "data": health
        }), 200
        
    except Exception as e:
        return jsonify({
            "success": False,
            "message": "Health check failed"
        }), 500













