import dayjs from "dayjs";

const dateFormatter = {
  install: (app) => {
    app.config.globalProperties.$formatDate = (
      dateTime,
      dateFormat = "YYYY-MM-DD hh:mm A"
    ) => {
      if (!dateTime) return;

      return dayjs(dateTime).format(dateFormat);
    };
  },
};

export default dateFormatter;
