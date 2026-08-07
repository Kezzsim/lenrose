// Builds a Typesense InstantSearch search client from resolved settings.

import TypesenseInstantSearchAdapter from "typesense-instantsearch-adapter";
import type { SearchConfig } from "../api/client";
import type { ResolvedTypesense } from "../state/settings";

export function createSearchClient(
  typesense: ResolvedTypesense,
  config: SearchConfig
) {
  const adapter = new TypesenseInstantSearchAdapter({
    server: {
      apiKey: typesense.apiKey,
      nodes: [
        {
          host: typesense.host,
          port: typesense.port,
          protocol: typesense.protocol,
        },
      ],
      cacheSearchResultsForSeconds: 2 * 60,
    },
    additionalSearchParameters: {
      query_by: config.queryBy.join(","),
    },
  });
  return adapter.searchClient;
}
