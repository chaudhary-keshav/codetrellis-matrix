"""
Apollo Client Subscription Extractor for CodeTrellis

Extracts Apollo Client subscription usage patterns:
- useSubscription() hook calls with variables and options
- client.subscribe() imperative subscriptions
- subscribeToMore() for combining query results with subscription data
- WebSocketLink / GraphQLWsLink for WebSocket transport
- split() link for routing between HTTP and WebSocket
- Subscription variables, fetchPolicy, skip
- onSubscriptionData / onData (v3.8+) / onError callbacks
- TypeScript generics

Supports:
- Apollo Client v1.x (basic subscriptions)
- Apollo Client v2.x (subscriptions-transport-ws via WebSocketLink)
- Apollo Client v3.x (@apollo/client subscriptions, graphql-ws via GraphQLWsLink)

Part of CodeTrellis v4.59 - Apollo Client Framework Support
"""

import re
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any


@dataclass
class ApolloSubscriptionInfo:
    """Information about a useSubscription() or client.subscribe() call."""
    name: str
    file: str = ""
    line_number: int = 0
    subscription_name: str = ""  # Name of the gql subscription document
    hook_name: str = "useSubscription"  # useSubscription, client.subscribe
    has_variables: bool = False
    has_skip: bool = False
    has_fetch_policy: bool = False
    has_on_subscription_data: bool = False  # v2/v3 (deprecated in v3.8+)
    has_on_data: bool = False  # v3.8+ replacement for onSubscriptionData
    has_on_complete: bool = False
    has_on_error: bool = False
    has_should_resubscribe: bool = False
    has_client: bool = False  # custom client
    has_context: bool = False
    has_typescript: bool = False
    type_params: str = ""
    is_exported: bool = False


@dataclass
class ApolloSubscribeToMoreInfo:
    """Information about a subscribeToMore() call."""
    file: str = ""
    line_number: int = 0
    document_name: str = ""  # Subscription document name
    has_variables: bool = False
    has_update_query: bool = False
    has_on_error: bool = False


class ApolloSubscriptionExtractor:
    """
    Extracts Apollo Client subscription definitions from source code.

    Detects:
    - useSubscription() hook calls with configuration
    - client.subscribe() imperative subscriptions
    - subscribeToMore() for live query updates
    - WebSocketLink / GraphQLWsLink configuration
    - split() link routing for subscriptions
    - Subscription callbacks and options
    - TypeScript generic annotations
    """

    # useSubscription() pattern
    USE_SUBSCRIPTION_PATTERN = re.compile(
        r'(?:export\s+)?(?:const|let|var)\s+(\{[^}]+\}|\w+)\s*=\s*'
        r'useSubscription\s*(?:<([^>]*)>)?\s*\(',
        re.MULTILINE
    )

    # client.subscribe() pattern
    CLIENT_SUBSCRIBE_PATTERN = re.compile(
        r'(?:client|apolloClient)\s*\.\s*subscribe\s*'
        r'(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # subscribeToMore() pattern
    SUBSCRIBE_TO_MORE_PATTERN = re.compile(
        r'subscribeToMore\s*(?:<([^>]*)>)?\s*\(\s*\{',
        re.MULTILINE
    )

    # WebSocketLink / GraphQLWsLink
    WS_LINK_PATTERN = re.compile(
        r'new\s+(WebSocketLink|GraphQLWsLink)\s*\(',
        re.MULTILINE
    )

    # split() link for subscription routing
    SPLIT_LINK_PATTERN = re.compile(
        r'(?:ApolloLink\.)?split\s*\(\s*(?:\(|function)',
        re.MULTILINE
    )

    # getMainDefinition (common in split for subscription detection)
    GET_MAIN_DEFINITION_PATTERN = re.compile(
        r'getMainDefinition\s*\(',
        re.MULTILINE
    )

    def extract(self, content: str, file_path: str = "") -> Dict[str, Any]:
        """
        Extract Apollo subscription patterns from source code.

        Args:
            content: Source code content
            file_path: Path to source file

        Returns:
            Dict with 'subscriptions', 'subscribe_to_more',
                       'has_ws_link', 'has_split_link', 'ws_link_type' keys
        """
        subscriptions: List[ApolloSubscriptionInfo] = []
        subscribe_to_more: List[ApolloSubscribeToMoreInfo] = []
        has_ws_link = False
        ws_link_type = ""  # WebSocketLink or GraphQLWsLink
        has_split_link = False

        # Extract useSubscription()
        for match in self.USE_SUBSCRIPTION_PATTERN.finditer(content):
            name = match.group(1).strip()
            type_params = match.group(2) or ""
            line_num = content[:match.start()].count('\n') + 1
            is_exported = 'export' in content[max(0, match.start() - 20):match.start() + 10]

            ctx_start = match.end()
            ctx_end = min(ctx_start + 500, len(content))
            ctx = content[ctx_start:ctx_end]

            sub_name = ""
            sname_match = re.match(r'\s*(\w+)', ctx)
            if sname_match:
                sub_name = sname_match.group(1)

            subscriptions.append(ApolloSubscriptionInfo(
                name=name,
                file=file_path,
                line_number=line_num,
                subscription_name=sub_name,
                hook_name="useSubscription",
                has_variables='variables' in ctx[:300],
                has_skip='skip' in ctx[:200] and ('skip:' in ctx[:200] or 'skip :' in ctx[:200]),
                has_fetch_policy='fetchPolicy' in ctx[:300],
                has_on_subscription_data='onSubscriptionData' in ctx[:400],
                has_on_data='onData' in ctx[:400],
                has_on_complete='onComplete' in ctx[:400],
                has_on_error='onError' in ctx[:400],
                has_should_resubscribe='shouldResubscribe' in ctx[:400],
                has_client='client:' in ctx[:300],
                has_context='context:' in ctx[:300],
                has_typescript=bool(type_params),
                type_params=type_params,
                is_exported=is_exported,
            ))

        # Extract client.subscribe()
        for match in self.CLIENT_SUBSCRIBE_PATTERN.finditer(content):
            type_params = match.group(1) or ""
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 400, len(content))
            ctx = content[ctx_start:ctx_end]

            sub_name = ""
            sname_match = re.search(r'query\s*:\s*(\w+)', ctx)
            if sname_match:
                sub_name = sname_match.group(1)

            subscriptions.append(ApolloSubscriptionInfo(
                name="client.subscribe",
                file=file_path,
                line_number=line_num,
                subscription_name=sub_name,
                hook_name="client.subscribe",
                has_variables='variables' in ctx[:300],
                has_fetch_policy='fetchPolicy' in ctx[:300],
                has_typescript=bool(type_params),
                type_params=type_params,
            ))

        # Extract subscribeToMore()
        for match in self.SUBSCRIBE_TO_MORE_PATTERN.finditer(content):
            line_num = content[:match.start()].count('\n') + 1

            ctx_start = match.end()
            ctx_end = min(ctx_start + 400, len(content))
            ctx = content[ctx_start:ctx_end]

            doc_name = ""
            dname_match = re.search(r'document\s*:\s*(\w+)', ctx)
            if dname_match:
                doc_name = dname_match.group(1)

            subscribe_to_more.append(ApolloSubscribeToMoreInfo(
                file=file_path,
                line_number=line_num,
                document_name=doc_name,
                has_variables='variables' in ctx[:300],
                has_update_query='updateQuery' in ctx[:400],
                has_on_error='onError' in ctx[:400],
            ))

        # Detect WebSocket link
        for match in self.WS_LINK_PATTERN.finditer(content):
            has_ws_link = True
            ws_link_type = match.group(1)

        # Detect split link
        if self.SPLIT_LINK_PATTERN.search(content):
            has_split_link = True

        return {
            'subscriptions': subscriptions,
            'subscribe_to_more': subscribe_to_more,
            'has_ws_link': has_ws_link,
            'ws_link_type': ws_link_type,
            'has_split_link': has_split_link,
        }
