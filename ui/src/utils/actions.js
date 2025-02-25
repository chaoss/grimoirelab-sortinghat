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
    { source: "confluence", icon: "fa:fab fa-confluence" },
    { source: "gerrit", icon: "$gerrit" },
    { source: "git", icon: "mdi-git" },
    { source: "github", icon: "mdi-github" },
    { source: "gitlab", icon: "mdi-gitlab" },
    { source: "dockerhub", icon: "mdi-docker" },
    { source: "jenkins", icon: "fa:fab fa-jenkins" },
    { source: "jira", icon: "mdi-jira" },
    { source: "launchpad", icon: "mdi-ubuntu" },
    { source: "linkedin", icon: "mdi-linkedin" },
    { source: "phorge", icon: "mdi-cog" },
    { source: "maniphest", icon: "fa:fab fa-phabricator" },
    { source: "mbox", icon: "mdi-email-newsletter" },
    { source: "meetup", icon: "fa:fab fa-meetup" },
    { source: "phabricator", icon: "fa:fab fa-phabricator" },
    { source: "pipermail", icon: "mdi-email-newsletter" },
    { source: "rss", icon: "mdi-rss" },
    { source: "slack", icon: "mdi-slack" },
    { source: "stackexchange", icon: "mdi-stack-exchange" },
    { source: "telegram", icon: "mdi-telegram" },
    { source: "twitter", icon: "mdi-twitter" },
  ];
  const otherSources = "Other sources";

  // Group identities by data source, emails and usernames
  const groupedData = identities.reduce((result, current) => {
    let source = current.source.toLowerCase().replace(/\s+/g, "");
    const sourceIcon = icons.find((icon) => icon.source === source);
    if (!sourceIcon) {
      source = otherSources;
    }
    if (!result.usernames) {
      result.usernames = new Set();
      result.emails = new Set();
      result.identitiesBysource = {};
    }
    if (current.email) {
      result.emails.add(current.email);
    }
    if (current.username) {
      result.usernames.add(
        JSON.stringify({
          [sourceIcon?.icon || "mdi-account-multiple"]: current.username,
        })
      );
    }
    if (result.identitiesBysource[source]) {
      result.identitiesBysource[source].identities.push(current);
    } else {
      result.identitiesBysource[source] = {
        name: source,
        identities: [current],
        icon: sourceIcon ? sourceIcon.icon : "mdi-account-multiple",
      };
    }
    return result;
  }, {});

  // Sort sources by alphabetical order and move "other" to end of list
  let sortedIdentities = Object.values(groupedData.identitiesBysource).sort(
    (a, b) => {
      if (a.name === otherSources) {
        return 1;
      } else if (b.name === otherSources) {
        return -1;
      }
      return a.name.localeCompare(b.name);
    }
  );

  return { identities: sortedIdentities, ...groupedData };
};

const formatIndividual = (individual) => {
  const { identities, emails, usernames } = groupIdentities(
    individual.identities
  );
  const formattedIndividual = {
    name: individual.profile.name,
    id: individual.profile.id,
    uuid: individual.mk,
    email: individual.profile.email,
    emails: emails,
    sources: identities.map((identity) => {
      return {
        name: identity.name,
        icon: identity.icon,
        count: identity.identities.length,
      };
    }),
    identities: identities,
    enrollments: individual.enrollments,
    gender: individual.profile.gender,
    country: individual.profile.country,
    isLocked: individual.isLocked,
    isBot: individual.profile.isBot,
    lastReviewed: individual.lastReviewed,
    lastModified: individual.lastModified,
    usernames: usernames,
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
