import { ref } from "vue";

export default function useModal() {
  const defaultValues = {
    isOpen: false,
    title: "",
    text: null,
    action: null,
    actionButtonLabel: null,
    actionButtonColor: "primary",
    dismissButtonLabel: "Close",
  };

  const modalProps = ref(Object.assign({}, defaultValues));

  const openModal = (options) => {
    modalProps.value = { isOpen: true, ...options };
  };

  const closeModal = () => {
    modalProps.value = { ...defaultValues };
  };

  return {
    modalProps,
    openModal,
    closeModal,
  };
}
