import logging

from sqlalchemy import TextClause, text

from ..config import Settings

_config = Settings.get_config()
_logger = logging.getLogger(_config.logging_default_logger_name)


def construct_eligibility_query(
    sql_queries_and_set_operators: list[tuple],
) -> TextClause:
    """
    Convert list of (SQL query, set operation) tuples
    into a single SQL query using the set operations
    """
    try:
        if not sql_queries_and_set_operators or not isinstance(
            sql_queries_and_set_operators, list
        ):
            return None

        query_parts = []
        for idx, (sql, set_op) in enumerate(sql_queries_and_set_operators):
            if not sql:
                continue
            if idx == 0:
                query_parts.append(sql)
            else:
                op = set_op if (set_op and set_op != "NONE") else "UNION"
                query_parts.append(f"{op} {sql}")

        final_query = " ".join(query_parts)

        _logger.debug("Constructed eligibility query: %s", final_query)
        return text(final_query)
    except Exception as _:
        return None


def construct_priority_query(sql_queries: list, registrant_ids: list) -> TextClause:
    """
    Convert list of SQL queries into a single SQL query using INTERSECT
    and filter the result to only include registrant_ids in the provided list.
    """
    try:
        if not sql_queries or not isinstance(sql_queries, list):
            return None

        intersect_query = " INTERSECT ".join(sql_queries)
        # Add the IN clause for registrant_ids
        if registrant_ids:
            # Prepare a comma-separated string of quoted IDs
            # If IDs are integers, don't quote; if strings, quote
            if all(isinstance(rid, int) for rid in registrant_ids):
                ids_str = ",".join(str(rid) for rid in registrant_ids)
            else:
                ids_str = ",".join(f"'{str(rid)}'" for rid in registrant_ids)
            # Wrap the intersect query as a subquery
            filtered_query = f"""
                SELECT * FROM (
                    {intersect_query}
                ) AS subquery
                WHERE link_registry_id IN ({ids_str})
            """
            _logger.debug("Constructed query for priority: %s", filtered_query)
            return text(filtered_query)
        else:
            _logger.debug("Constructed query for priority: %s", intersect_query)
            return text(intersect_query)
    except Exception as _:
        return None
