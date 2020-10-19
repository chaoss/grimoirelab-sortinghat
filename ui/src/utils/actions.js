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

export { mergeIndividuals };
