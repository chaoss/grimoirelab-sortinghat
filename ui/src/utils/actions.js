const mergeIndividuals = (individuals, action, dialog) => {
  if (individuals.length !== new Set(individuals).size) {
    return;
  }
  const [toIndividual, ...rest] = individuals;
  const fromIndividuals = rest.map(individual =>
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
    title: "Merge the selected items?",
    text: "",
    action: () => action(fromUuids, toUuid)
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
    action: () => action(fromUuid, toUuid)
  });
};

const groupIdentities = identities => {
  const icons = [
    { source: "git", icon: "mdi-git" },
    { source: "github", icon: "mdi-github" },
    { source: "gitlab", icon: "mdi-gitlab" },
    { source: "dockerhub", icon: "mdi-docker" },
    { source: "jira", icon: "mdi-jira" },
    { source: "rss", icon: "mdi-rss" },
    { source: "slack", icon: "mdi-slack" },
    { source: "stackexchange", icon: "mdi-stack-exchange" },
    { source: "telegram", icon: "mdi-telegram" },
    { source: "twitter", icon: "mdi-twitter" }
  ];
  const otherSources = "Other sources";
  // Group identities by data source
  const groupedIdentities = identities.reduce((result, val) => {
    let source = val.source.toLowerCase().replace(/\s+/g, "");
    const sourceIcon = icons.find(icon => icon.source === source);
    if (!sourceIcon) {
      source = otherSources;
    }
    if (result[source]) {
      result[source].identities.push(val);
    } else {
      result[source] = {
        name: source,
        identities: [val],
        icon: sourceIcon ? sourceIcon.icon : "mdi-account-multiple"
      };
    }
    return result;
  }, {});

  // Sort identities by alphabetical order
  let sortedIdentities = Object.values(groupedIdentities).sort((a, b) =>
    a.name.localeCompare(b.name)
  );

  // Move "other" identities to end of list
  sortedIdentities.push(
    ...sortedIdentities.splice(
      sortedIdentities.findIndex(identity => identity.name == otherSources),
      1
    )
  );

  return sortedIdentities;
};

const formatIndividuals = individuals => {
  const formattedList = individuals.map(item => {
    return {
      name: item.profile.name,
      id: item.profile.id,
      email: item.profile.email,
      username: item.identities[0].username,
      organization: item.enrollments[0]
        ? item.enrollments[0].organization.name
        : "",
      sources: groupIdentities(item.identities).map(identity => {
        return { name: identity.name, icon: identity.icon };
      }),
      gender: item.profile.gender,
      country: item.profile.country,
      identities: groupIdentities(item.identities),
      enrollments: item.enrollments,
      isLocked: item.isLocked,
      isBot: item.profile.isBot,
      uuid: item.mk,
      isSelected: false
    };
  });

  return formattedList;
};

export { mergeIndividuals, moveIdentity, groupIdentities, formatIndividuals };
