import gql from "graphql-tag";

const GET_INDIVIDUAL_BYUUID = gql`
  query GetIndividual($uuid: String!) {
    individuals(filters: { uuid: $uuid }) {
      entities {
        mk
        identities {
          name
        }
        profile {
          id
          name
        }
      }
    }
  }
`;

const GET_INDIVIDUALS = gql`
  query GetIndividuals($page: Int!, $pageSize: Int!) {
    individuals(page: $page, pageSize: $pageSize) {
      entities {
        mk
        identities {
          name
        }
        profile {
          id
          name
        }
      }
      pageInfo {
        page
        pageSize
        numPages
        hasNext
        hasPrev
        startIndex
        endIndex
        totalResults
      }
    }
  }
`;

const getIndividualByUuid = (apollo, uuid) => {
  let response = apollo.query({
    query: GET_INDIVIDUAL_BYUUID,
    variables: {
      uuid: uuid
    }
  });
  return response;
};

const getIndividuals = (apollo, page, pageSize) => {
  if (!page) {
    page = 1;
  }
  if (!pageSize) {
    pageSize = 10;
  }
  let response = apollo.query({
    query: GET_INDIVIDUALS,
    variables: {
      page: page,
      pageSize: pageSize
    }
  });
  return response;
};

export { getIndividuals, getIndividualByUuid };
