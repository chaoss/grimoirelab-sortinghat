const mergeIndividuals = (individuals, action, dialog) => {
  const [toIndividual, ...rest] = individuals;
  const fromIndividuals = rest.map(individual => individual.uuid);
  confirmMerge(dialog, action, fromIndividuals, toIndividual.uuid);
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
