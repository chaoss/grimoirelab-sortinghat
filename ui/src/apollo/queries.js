import gql from "graphql-tag";
import { CHANGELOG, FULL_INDIVIDUAL } from "./fragments";

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
        changelog {
          ...changelog
        }
      }
    }
  }
  ${FULL_INDIVIDUAL}
  ${CHANGELOG}
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
    $orderBy: String
  ) {
    organizations(
      page: $page
      pageSize: $pageSize
      filters: $filters
      orderBy: $orderBy
    ) {
      entities {
        id
        name
        enrollments {
          id
        }
        domains {
          domain
          isTopDomain
        }
        aliases {
          alias
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

const GET_IMPORTERS = gql`
  query getImporters {
    identitiesImportersTypes {
      name
      args
    }
  }
`;

const GET_IMPORT_IDENTITIES_TASKS = gql`
  query getImportIdentitiesTasks(
    $page: Int
    $pageSize: Int
    $filters: ScheduledTasksFilterType!
  ) {
    scheduledTasks(page: $page, pageSize: $pageSize, filters: $filters) {
      entities {
        id
        interval
        args
        jobId
        lastExecution
        scheduledDatetime
        failures
        executions
        failed
      }
    }
  }
`;

const GET_ORGANIZATION = gql`
  query getOrganization($filters: OrganizationFilterType!) {
    organizations(filters: $filters) {
      entities {
        name
        domains {
          id
          domain
          isTopDomain
        }
        aliases {
          alias
        }
      }
    }
  }
`;

const GET_SCHEDULED_TASKS = gql`
  query getScheduledTasks($filters: ScheduledTasksFilterType) {
    scheduledTasks(filters: $filters) {
      entities {
        id
        jobType
        interval
        args
        jobId
        lastExecution
        failed
      }
    }
  }
`;

const FIND_ORGANIZATION = gql`
  query findOrganization(
    $page: Int
    $pageSize: Int
    $filters: OrganizationFilterType
  ) {
    organizations(page: $page, pageSize: $pageSize, filters: $filters) {
      entities {
        id
        name
        aliases {
          alias
        }
      }
    }
  }
`;

const getIndividualByUuid = (apollo, uuid) => {
  let response = apollo.query({
    query: GET_INDIVIDUAL_BYUUID,
    variables: {
      uuid: uuid,
    },
    fetchPolicy: "cache-first",
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

const getPaginatedOrganizations = (
  apollo,
  currentPage,
  pageSize,
  filters,
  orderBy
) => {
  let response = apollo.query({
    query: GET_PAGINATED_ORGANIZATIONS,
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

const getImporterTypes = (apollo) => {
  return apollo.query({
    query: GET_IMPORTERS,
  });
};

const getImportIdentitiesTasks = (apollo, page, pageSize, filters = {}) => {
  return apollo.query({
    query: GET_IMPORT_IDENTITIES_TASKS,
    variables: {
      page: page,
      pageSize: pageSize,
      filters: Object.assign(filters, { jobType: "import_identities" }),
    },
    fetchPolicy: "no-cache",
  });
};

const getOrganization = (apollo, name) => {
  return apollo.query({
    query: GET_ORGANIZATION,
    variables: {
      filters: {
        name: name,
      },
    },
  });
};

const getScheduledTasks = (apollo, jobType, backend) => {
  return apollo.query({
    query: GET_SCHEDULED_TASKS,
    variables: {
      filters: {
        jobType,
        backend,
      },
    },
    fetchPolicy: "no-cache",
  });
};

const findOrganization = (apollo, page, pageSize, filters) => {
  return apollo.query({
    query: FIND_ORGANIZATION,
    variables: {
      page,
      pageSize,
      filters,
    },
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
  getRecommendedMergesCount,
  getPaginatedMergeRecommendations,
  getImporterTypes,
  getImportIdentitiesTasks,
  getOrganization,
  getScheduledTasks,
  findOrganization,
  GET_INDIVIDUAL_BYUUID,
  GET_ORGANIZATION,
};
