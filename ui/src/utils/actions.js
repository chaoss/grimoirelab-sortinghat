const mergeIndividuals = (individuals, action, dialog) => {
  if (individuals.length !== new Set(individuals).size) {
    return;
  }
  const [toIndividual, ...rest] = individuals;
  const fromIndividuals = rest.map((individual) =>
    individual.uuid ? individual.uuid : individual
  );
  confirmMerge(
    dialog,
    action,
    fromIndividuals,
    toIndividual.uuid || toIndividual
  );
};

const confirmMerge = (dialog, action, fromUuids, toUuid) => {
  Object.assign(dialog, {
    open: true,
    title: "Merge the selected individuals?",
    text: "",
    action: () => action(fromUuids, toUuid),
  });
};

const moveIdentity = (fromUuid, toUuid, action, dialog) => {
  if (fromUuid === toUuid) {
    return;
  }
  Object.assign(dialog, {
    open: true,
    title: "Move identity to this individual?",
    text: "",
    action: () => action(fromUuid, toUuid),
  });
};

const groupIdentities = (identities) => {
  const icons = [
    { source: "git", icon: "mdi-git" },
    { source: "github", icon: "mdi-github" },
    { source: "gitlab", icon: "mdi-gitlab" },
    { source: "dockerhub", icon: "mdi-docker" },
    { source: "jira", icon: "mdi-jira" },
    { source: "linkedin", icon: "mdi-linkedin" },
    { source: "rss", icon: "mdi-rss" },
    { source: "slack", icon: "mdi-slack" },
    { source: "stackexchange", icon: "mdi-stack-exchange" },
    { source: "telegram", icon: "mdi-telegram" },
    { source: "twitter", icon: "mdi-twitter" },
  ];
  const otherSources = "Other sources";
  // Group identities by data source
  const groupedIdentities = identities.reduce((result, val) => {
    let source = val.source.toLowerCase().replace(/\s+/g, "");
    const sourceIcon = icons.find((icon) => icon.source === source);
    if (!sourceIcon) {
      source = otherSources;
    }
    if (result[source]) {
      result[source].identities.push(val);
    } else {
      result[source] = {
        name: source,
        identities: [val],
        icon: sourceIcon ? sourceIcon.icon : "mdi-account-multiple",
      };
    }
    return result;
  }, {});

  // Sort sources by alphabetical order and move "other" to end of list
  let sortedIdentities = Object.values(groupedIdentities).sort((a, b) => {
    if (a.name === otherSources) {
      return 1;
    } else if (b.name === otherSources) {
      return -1;
    }
    return a.name.localeCompare(b.name);
  });

  return sortedIdentities;
};

const formatIndividual = (individual) => {
  const formattedIndividual = {
    name: individual.profile.name,
    id: individual.profile.id,
    uuid: individual.mk,
    email: individual.profile.email,
    sources: groupIdentities(individual.identities).map((identity) => {
      return {
        name: identity.name,
        icon: identity.icon,
        count: identity.identities.length,
      };
    }),
    identities: groupIdentities(individual.identities),
    enrollments: individual.enrollments,
    gender: individual.profile.gender,
    country: individual.profile.country,
    isLocked: individual.isLocked,
    isBot: individual.profile.isBot,
  };

  if (individual.enrollments && individual.enrollments.length > 0) {
    const organization = individual.enrollments.findLast(
      (enrollment) => !enrollment.group.parentOrg
    )?.group.name;
    Object.assign(formattedIndividual, { organization: organization });
  }
  if (individual.matchRecommendationSet) {
    const matchRecommendations = individual.matchRecommendationSet.map(
      (rec) => {
        return {
          id: rec.id,
          individual: formatIndividual(rec.individual),
        };
      }
    );
    Object.assign(formattedIndividual, {
      matchRecommendations: matchRecommendations,
    });
  }
  return formattedIndividual;
};

const formatIndividuals = (individuals) => {
  return individuals.map((item) => formatIndividual(item));
};

export {
  mergeIndividuals,
  moveIdentity,
  groupIdentities,
  formatIndividual,
  formatIndividuals,
};
