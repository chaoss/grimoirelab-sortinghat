import gql from "graphql-tag";

const GET_INDIVIDUAL_BYUUID = gql`
  query GetIndividual($uuid: String!) {
    individuals(filters: { uuid: $uuid }) {
      entities {
        mk
        isLocked
        profile {
          name
          id
          email
          isBot
          gender
          country {
            code
            name
          }
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

const GET_PAGINATED_INDIVIDUALS = gql`
  query GetIndividuals(
    $page: Int!
    $pageSize: Int!
    $filters: IdentityFilterType
    $orderBy: String
  ) {
    individuals(
      page: $page
      pageSize: $pageSize
      filters: $filters
      orderBy: $orderBy
    ) {
      entities {
        mk
        isLocked
        profile {
          name
          id
          email
          isBot
          gender
          country {
            code
            name
          }
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
      pageInfo {
        page
        pageSize
        numPages
        totalResults
      }
    }
  }
`;

const GET_PAGINATED_ORGANIZATIONS = gql`
  query GetOrganizations(
    $page: Int!
    $pageSize: Int!
    $filters: OrganizationFilterType
  ) {
    organizations(page: $page, pageSize: $pageSize, filters: $filters) {
      entities {
        id
        name
        enrollments {
          id
        }
        domains {
          domain
        }
      }
      pageInfo {
        page
        pageSize
        numPages
        totalResults
      }
    }
  }
`;

const GET_COUNTRIES = gql`
  query getCountries {
    countries(pageSize: 500) {
      entities {
        code
        name
      }
    }
  }
`;

const GET_JOBS = gql`
  query getJobs($page: Int!, $pageSize: Int!) {
    jobs(page: $page, pageSize: $pageSize) {
      entities {
        jobId
        status
        jobType
        errors
        enqueuedAt
      }
      pageInfo {
        page
        numPages
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

const getPaginatedIndividuals = (
  apollo,
  currentPage,
  pageSize,
  filters,
  orderBy
) => {
  let response = apollo.query({
    query: GET_PAGINATED_INDIVIDUALS,
    variables: {
      page: currentPage,
      pageSize: pageSize,
      filters: filters,
      orderBy: orderBy
    },
    fetchPolicy: "no-cache"
  });
  return response;
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

const getPaginatedOrganizations = (apollo, currentPage, pageSize, filters) => {
  let response = apollo.query({
    query: GET_PAGINATED_ORGANIZATIONS,
    variables: {
      page: currentPage,
      pageSize: pageSize,
      filters: filters
    },
    fetchPolicy: "no-cache"
  });
  return response;
};

const getCountries = apollo => {
  let response = apollo.query({
    query: GET_COUNTRIES
  });
  return response;
};

const getJobs = (apollo, page, pageSize) => {
  let response = apollo.query({
    query: GET_JOBS,
    variables: {
      page: page,
      pageSize: pageSize
    }
  });
  return response;
};

export {
  getCountries,
  getIndividuals,
  getIndividualByUuid,
  getProfileByUuid,
  getPaginatedIndividuals,
  getPaginatedOrganizations,
  getJobs
};
