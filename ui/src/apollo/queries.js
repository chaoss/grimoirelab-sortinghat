import gql from "graphql-tag";
import { FULL_INDIVIDUAL } from "./fragments";

const GET_INDIVIDUAL_BYUUID = gql`
  query GetIndividual($uuid: String!) {
    individuals(filters: { uuid: $uuid }) {
      entities {
        ...individual
        matchRecommendationSet {
          id
          individual {
            ...individual
          }
        }
      }
    }
  }
  ${FULL_INDIVIDUAL}
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
          group {
            name
            type
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
        ...individual
      }
      pageInfo {
        page
        pageSize
        numPages
        totalResults
      }
    }
  }
  ${FULL_INDIVIDUAL}
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
          individual {
            mk
          }
        }
        domains {
          domain
          isTopDomain
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

const GET_TEAMS = gql`
  query GetTeams($filters: TeamFilterType) {
    teams(pageSize: 500, filters: $filters) {
      entities {
        name
        numchild
        id
        enrollments {
          individual {
            mk
          }
        }
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

const GET_GROUPS = gql`
  query getGroups($page: Int, $pageSize: Int, $filters: GroupFilterType) {
    groups(page: $page, pageSize: $pageSize, filters: $filters) {
      entities {
        id
        name
        numchild
      }
      pageInfo {
        page
        numPages
        totalResults
      }
    }
  }
`;

const GET_TOTAL_RECOMMENDED_MERGES = gql`
  query recommendedMergeNumber {
    recommendedMerge {
      pageInfo {
        totalResults
      }
    }
  }
`;

const GET_PAGINATED_RECOMMENDED_MERGE = gql`
  query recommendedMerge($page: Int, $pageSize: Int) {
    recommendedMerge(page: $page, pageSize: $pageSize) {
      entities {
        id
        individual1 {
          ...individual
        }
        individual2 {
          ...individual
        }
      }
      pageInfo {
        totalResults
        page
        pageSize
        numPages
        hasNext
      }
    }
  }
  ${FULL_INDIVIDUAL}
`;

const getIndividualByUuid = (apollo, uuid) => {
  let response = apollo.query({
    query: GET_INDIVIDUAL_BYUUID,
    variables: {
      uuid: uuid,
    },
    fetchPolicy: "no-cache",
  });
  return response;
};

const getIndividuals = {
  currentPage: 1,
  numPages: 1,
  pageSize: 10,
  query: async function (apollo, pageSize) {
    let self = this;
    if (pageSize) {
      self.pageSize = pageSize;
    }
    let response = await apollo.query({
      query: GET_INDIVIDUALS,
      variables: {
        page: self.currentPage,
        pageSize: pageSize,
      },
    });
    self.numPages = response.data.individuals.pageInfo.numPages;
    if (self.currentPage > self.numPages) {
      return undefined;
    }
    self.currentPage++;
    return response;
  },
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
      orderBy: orderBy,
    },
    fetchPolicy: "no-cache",
  });
  return response;
};

const getProfileByUuid = (apollo, uuid) => {
  let response = apollo.query({
    query: GET_PROFILE_BYUUID,
    variables: {
      uuid: uuid,
    },
  });
  return response;
};

const getPaginatedOrganizations = (apollo, currentPage, pageSize, filters) => {
  let response = apollo.query({
    query: GET_PAGINATED_ORGANIZATIONS,
    variables: {
      page: currentPage,
      pageSize: pageSize,
      filters: filters,
    },
    fetchPolicy: "no-cache",
  });
  return response;
};

const getCountries = (apollo) => {
  let response = apollo.query({
    query: GET_COUNTRIES,
  });
  return response;
};

const getJobs = (apollo, page, pageSize) => {
  let response = apollo.query({
    query: GET_JOBS,
    variables: {
      page: page,
      pageSize: pageSize,
    },
    fetchPolicy: "no-cache",
  });
  return response;
};

const getTeams = (apollo, filters) => {
  let response = apollo.query({
    query: GET_TEAMS,
    variables: {
      filters: filters,
    },
    fetchPolicy: "no-cache",
  });
  return response;
};

const getGroups = (apollo, page, pageSize, filters) => {
  let response = apollo.query({
    query: GET_GROUPS,
    variables: {
      page: page,
      pageSize: pageSize,
      filters: filters,
    },
    fetchPolicy: "no-cache",
  });
  return response;
};

const getRecommendedMergesCount = (apollo) => {
  return apollo.query({
    query: GET_TOTAL_RECOMMENDED_MERGES,
    fetchPolicy: "no-cache",
  });
};

const getPaginatedMergeRecommendations = (apollo, page, pageSize) => {
  return apollo.query({
    query: GET_PAGINATED_RECOMMENDED_MERGE,
    variables: {
      page: page,
      pageSize: pageSize,
    },
    fetchPolicy: "no-cache",
  });
};

export {
  getCountries,
  getIndividuals,
  getIndividualByUuid,
  getProfileByUuid,
  getPaginatedIndividuals,
  getPaginatedOrganizations,
  getTeams,
  getJobs,
  getGroups,
  getRecommendedMergesCount,
  getPaginatedMergeRecommendations,
};
