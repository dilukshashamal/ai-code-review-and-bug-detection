import { ApolloClient, HttpLink, InMemoryCache } from "@apollo/client";

const graphqlEndpoint =
  import.meta.env.VITE_GRAPHQL_ENDPOINT ?? "http://localhost:8000/graphql";

export const apolloClient = new ApolloClient({
  link: new HttpLink({
    uri: graphqlEndpoint,
  }),
  cache: new InMemoryCache(),
});
