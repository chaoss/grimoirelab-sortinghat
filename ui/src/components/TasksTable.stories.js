import TasksTable from "./TasksTable.vue";

export default {
  title: "TasksTable",
  excludeStories: /.*Data$/,
};

const template = `
  <tasks-table
    :fetch-backends="fetchBackends"
    :fetch-tasks="fetchTasks"
    :create-task="() => {}"
    :delete-task="deleteTask"
    :edit-task="() => {}"
  />
`;

export const Default = () => ({
  components: { TasksTable },
  template: template,
  data: () => ({
    backends: {
      data: {
        identitiesImportersTypes: [
          { name: "mailmap", args: ["url"] },
          { name: "external plugin", args: ["url", "token"] },
        ],
      },
    },
    tasks: {
      data: {
        scheduledTasks: {
          entities: [
            {
              id: 1,
              args: {
                backend_name: "mailmap",
                url: "http://test.com",
              },
              interval: 43800,
              lastExecution: "2023-03-14T14:21:10",
              failed: true,
              scheduledDatetime: "2023-03-14T14:56:10",
              failures: 1,
              executions: 22,
            },
            {
              id: 2,
              args: {
                backend_name: "external plugin",
                url: "http://test.com",
                token: "XXXX",
              },
              interval: 0,
              lastExecution: "2023-03-12T11:01:40",
              failed: false,
              failures: 0,
              executions: 1,
            },
          ],
        },
      },
    },
  }),
  methods: {
    fetchBackends() {
      return this.backends;
    },
    fetchTasks() {
      return this.tasks;
    },
    deleteTask(id) {
      this.tasks.data.scheduledTasks.entities =
        this.tasks.data.scheduledTasks.entities.filter(
          (task) => task.id !== id,
        );
      return {
        data: {
          deleteImportIdentitiesTask: {
            deleted: true,
          },
        },
      };
    },
  },
});

export const Empty = () => ({
  components: { TasksTable },
  template: template,
  data: () => ({
    backends: {
      data: {
        identitiesImportersTypes: [
          { name: "mailmap", args: ["url"] },
          { name: "external plugin", args: ["url", "token"] },
        ],
      },
    },
    tasks: {
      data: {
        importIdentitiesTask: {
          entities: [],
        },
      },
    },
  }),
  methods: {
    fetchBackends() {
      return this.backends;
    },
    fetchTasks() {
      return this.tasks;
    },
    deleteTask() {
      return;
    },
  },
});
