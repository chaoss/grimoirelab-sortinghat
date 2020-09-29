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
        isLocked
        identities {
          name
          source
          uuid
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

const GET_PROFILE_BYUUID = gql`
  query GetProfileByUuid($uuid: String!) {
    individuals(filters: { uuid: $uuid }) {
      entities {
        isLocked
        profile {
          name
        }
        identities {
          name
          source
          email
          uuid
          username
        }
        enrollments {
          start
          end
          organization {
            name
          }
        }
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

const getIndividuals = {
  currentPage: 1,
  numPages: 1,
  pageSize: 10,
  query: async function(apollo, pageSize) {
    let self = this;
    if (pageSize) {
      self.pageSize = pageSize;
    }
    let response = await apollo.query({
      query: GET_INDIVIDUALS,
      variables: {
        page: self.currentPage,
        pageSize: pageSize
      }
    });
    self.numPages = response.data.individuals.pageInfo.numPages;
    if (self.currentPage > self.numPages) {
      return undefined;
    }
    self.currentPage++;
    return response;
  }
};

const getProfileByUuid = (apollo, uuid) => {
  let response = apollo.query({
    query: GET_PROFILE_BYUUID,
    variables: {
      uuid: uuid
    }
  });
  return response;
};

export { getIndividuals, getIndividualByUuid, getProfileByUuid };
