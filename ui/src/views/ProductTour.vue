<template>
  <v-main>
    <work-space
      class="ma-md-8 mt-md-6"
      :enroll="mockMethod"
      :individuals="savedIndividuals"
      :merge-items="mockMethod"
      :move-item="mockMethod"
      ref="workspace"
    />
    <v-row>
      <v-col lg="8" sm="12" class="pa-0 mr-lg-8">
        <individuals-table
          class="individuals"
          is-expandable
          outlined
          :fetch-page="getIndividuals"
          :delete-item="mockMethod"
          :merge-items="mockMethod"
          :unmerge-items="mockMethod"
          :move-item="mockMethod"
          :add-identity="mockMethod"
          :updateProfile="mockMethod"
          :enroll="mockMethod"
          :fetch-organizations="getOrganizations"
          :get-countries="mockMethod"
          :lock-individual="mockMethod"
          :unlock-individual="mockMethod"
          :withdraw="mockMethod"
          :update-enrollment="mockMethod"
          :recommend-matches="mockMethod"
          @hook:updated="atChildMounted"
          ref="individualstable"
        />
      </v-col>
      <v-col class="pa-0 organizations mt-8 mt-lg-0">
        <organizations-table
          :fetch-page="getOrganizations"
          :enroll="mockMethod"
          :add-organization="mockMethod"
          :add-domain="mockMethod"
          :delete-domain="mockMethod"
          :delete-organization="mockMethod"
          :add-team="mockMethod"
          :delete-team="mockMethod"
          :fetch-teams="mockMethod"
          ref="organizationstable"
        />
      </v-col>
    </v-row>
  </v-main>
</template>
<script>
import IndividualsTable from "../components/IndividualsTable";
import OrganizationsTable from "../components/OrganizationsTable";
import WorkSpace from "../components/WorkSpace";

const mockedIndividualsQuery = {
  data: {
    individuals: {
      entities: [
        {
          mk: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6",
          isLocked: false,
          profile: {
            name: "Tom Marvolo Riddle",
            id: "1",
            email: "triddle@example.com",
            isBot: false,
          },
          identities: [
            {
              name: "Tom Marvolo Riddle",
              source: "GitLab",
              email: "triddle@example.net",
              uuid: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6",
              username: "triddle",
            },
            {
              uuid: "33697bad47122a2093d9edbbe179a72298971fd1",
              name: "Voldemort",
              email: "-",
              username: "voldemort",
              source: "github",
            },
          ],
          enrollments: [
            {
              group: {
                name: "Slytherin",
                id: "2",
              },
              start: "1938-09-01T00:00:00+00:00",
              end: "1998-05-02T00:00:00+00:00",
            },
          ],
        },
        {
          mk: "375458370ac0323bfb2e5a153e086551ef628d53",
          isLocked: false,
          profile: {
            name: "Voldemort",
            id: "3",
            email: "",
            isBot: false,
          },
          identities: [
            {
              uuid: "375458370ac0323bfb2e5a153e086551ef628d53",
              name: "",
              email: "voldemort@example.net",
              username: "voldemort",
              source: "git",
            },
          ],
          enrollments: [],
        },
        {
          mk: "164e41c60c28698ac30b0d17176d3e720e036918",
          isLocked: false,
          profile: {
            name: "Harry Potter",
            id: "2",
            email: "hpotter@example.com",
            isBot: false,
          },
          identities: [
            {
              name: "Harry Potter",
              source: "GitHub",
              email: "hpotter@example.net",
              uuid: "164e41c60c28698ac30b0d17176d3e720e036918",
              username: "-",
            },
            {
              uuid: "06e6903c91180835b6ee91dd56782c6ca72bc562",
              name: "H. Potter",
              email: "hpotter@example.net",
              username: "potter",
              source: "git",
            },
          ],
          enrollments: [
            {
              group: {
                name: "Griffyndor",
                id: "2",
              },
              start: "1991-09-01",
              end: "1997-06-02T00:00:00+00:00",
            },
          ],
        },
        {
          mk: "e4135c5c747dc69262cd4120a5c5ee51d07a9904",
          isLocked: true,
          profile: {
            name: "Hermione Granger",
            id: "5",
            email: "hgranger@example.com",
            isBot: false,
          },
          identities: [
            {
              uuid: "e4135c5c747dc69262cd4120a5c5ee51d07a9904",
              name: "Hermione Granger",
              email: "hgranger@example.net",
              username: "hermione",
              source: "gitlab",
            },
          ],
          enrollments: [
            {
              group: {
                name: "Griffyndor",
                id: "2",
              },
              start: "1991-09-01",
              end: "1997-06-02T00:00:00+00:00",
            },
          ],
        },
        {
          mk: "66bc656d28a1522b650d537c9142be2e5c9e3b55",
          isLocked: false,
          profile: {
            name: "Ron Weasley",
            id: "4",
            email: "rweasley@example.com",
            isBot: false,
          },
          identities: [
            {
              uuid: "66bc656d28a1522b650d537c9142be2e5c9e3b55",
              name: "Ron Weasley",
              email: "rweasley@example.net",
              username: "",
              source: "git",
            },
          ],
          enrollments: [
            {
              group: {
                name: "Griffyndor",
                id: "2",
              },
              start: "1991-09-01",
              end: "1997-06-02T00:00:00+00:00",
            },
          ],
        },
        {
          mk: "de85900c79d5dbe782f65ce0e04f269c4cd2f7fb",
          isLocked: false,
          profile: {
            name: "Albus Dumbledore",
            id: "6",
            email: "albus.dumbledore@example.com",
            isBot: false,
          },
          identities: [
            {
              uuid: "4df20c13824ce60c2249a9b947d6c55dc0ba26a4",
              name: "Albus Dumbledore",
              email: "headmaster@hogwarts.net",
              username: "albus",
              source: "GitLab",
            },
            {
              uuid: "de85900c79d5dbe782f65ce0e04f269c4cd2f7fb",
              name: "Albus Dumbledore",
              email: "adumbledore@example.net",
              username: "albus",
              source: "Jira",
            },
          ],
          enrollments: [],
        },
      ],
      pageInfo: {
        page: 1,
        pageSize: 10,
        numPages: 1,
        totalResults: 6,
      },
    },
  },
};

const mockedOrganizationsQuery = {
  data: {
    organizations: {
      entities: [
        {
          id: 1,
          name: "Griffyndor",
          enrollments: [
            { id: 1, individual: { mk: 1 } },
            { id: 2, individual: { mk: 2 } },
            { id: 3, individual: { mk: 3 } },
          ],
          domains: [{ domain: "griffyndor.hogwarts.edu" }],
        },
        {
          id: 2,
          name: "Slytherin",
          enrollments: [{ id: 1, individual: { mk: 1 } }],
          domains: [{ domain: "slytherin.hogwarts.edu" }],
        },
        {
          id: 3,
          name: "Ravenclaw",
          enrollments: [],
          domains: [{ domain: "ravenclaw.hogwarts.edu" }],
        },
        {
          id: 4,
          name: "Hufflepuff",
          enrollments: [],
          domains: [{ domain: "hufflepuff.hogwarts.edu" }],
        },
      ],
      pageInfo: {
        page: 1,
        pageSize: 10,
        numPages: 1,
        totalResults: 4,
      },
    },
  },
};

export default {
  name: "ProductTour",
  components: {
    IndividualsTable,
    OrganizationsTable,
    WorkSpace,
  },
  data: () => ({
    tour: null,
    individuals: mockedIndividualsQuery,
    organizations: mockedOrganizationsQuery,
    savedIndividuals: [
      {
        name: "Tom Marvolo Riddle",
        id: "1",
        uuid: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6",
        email: "triddle@example.com",
        sources: [
          { name: "github", icon: "mdi-github", count: 1 },
          { name: "gitlab", icon: "mdi-gitlab", count: 1 },
        ],
        identities: [
          {
            name: "github",
            identities: [
              {
                uuid: "33697bad47122a2093d9edbbe179a72298971fd1",
                name: "Voldemort",
                email: "-",
                username: "voldemort",
                source: "github",
              },
            ],
            icon: "mdi-github",
          },
          {
            name: "gitlab",
            identities: [
              {
                name: "Tom Marvolo Riddle",
                source: "GitLab",
                email: "triddle@example.net",
                uuid: "1f1a9e56dedb45f5969413eeb4442d982e33f0f6",
                username: "triddle",
              },
            ],
            icon: "mdi-gitlab",
          },
        ],
        enrollments: [
          {
            group: { name: "Slytherin", id: "2" },
            start: "1938-09-01T00:00:00+00:00",
            end: "1998-05-02T00:00:00+00:00",
          },
        ],
        isLocked: false,
        isBot: false,
        isSelected: false,
        organization: "Slytherin",
      },
    ],
  }),
  methods: {
    createTour() {
      this.tour = this.$shepherd({
        useModalOverlay: true,
        defaultStepOptions: {
          classes: "shepherd-theme-custom",
          when: {
            show() {
              const currentStep = this.tour.getCurrentStep();
              const currentStepElement = currentStep?.getElement();
              const footer =
                currentStepElement?.querySelector(".shepherd-footer");
              const progress = document.createElement("span");
              progress.innerText = `${
                this.tour.steps.indexOf(currentStep) + 1
              }/${this.tour.steps.length}`;
              footer?.insertBefore(
                progress,
                currentStepElement.querySelector(".shepherd-button")
              );
            },
          },
        },
      });

      const lockElement = document
        .querySelector(".mdi-lock:not(.icon--hidden)")
        .closest(".v-list-item__title");
      this.tour.addSteps([
        {
          text: `<p>SortingHat is the GrimoireLab tool to manage identities.</p>
            <p>Here are some quick tips to get you started.</p>`,
          title: "Welcome to SortingHat",
          buttons: [
            {
              text: "Skip the tour",
              action: this.endTour,
              secondary: true,
            },
            {
              text: "Start",
              action: this.tour.next,
            },
          ],
        },
        {
          attachTo: {
            element: this.$refs.individualstable.$el,
            on: "top",
          },
          text: "Each individual has a profile that may consist of several identities. People may have different usernames in GitHub and GitLab, or use several emails in git.",
          title: "Manage community members across different sources",
          buttons: [
            {
              text: "Skip the tour",
              action: this.endTour,
              secondary: true,
            },
            {
              text: "Next",
              action: this.tour.next,
            },
          ],
        },
        {
          attachTo: {
            element: this.$refs.individualstable.$refs.indv_entry_0.$el,
            on: "right",
          },
          text: `<img src="${process.env.BASE_URL}images/merge.gif" class="mx-auto">
            To unify different identities into a single profile, drag and drop them into the main one. You can select and drag several items at once.`,
          title: "Drag and drop to merge identities",
          buttons: [
            {
              text: "Skip the tour",
              action: this.endTour,
              secondary: true,
            },
            {
              text: "Next",
              action: this.tour.next,
            },
          ],
        },
        {
          attachTo: {
            element: this.$refs.organizationstable.$el,
            on: "top",
          },
          text: "Each individual can be related to one or more organizations, for different time periods.",
          title: "Manage community member affiliations",
          buttons: [
            {
              text: "Skip the tour",
              action: this.endTour,
              secondary: true,
            },
            {
              text: "Next",
              action: this.tour.next,
            },
          ],
        },
        {
          attachTo: {
            element: this.$refs.organizationstable.$refs.org_entry_0.$el,
            on: "left",
          },
          text: `<img src="${process.env.BASE_URL}images/affiliate.gif" class="mx-auto">
            You can also drag and drop organizations to affiliate individuals.`,
          title: "Drag and drop to affiliate",
          buttons: [
            {
              text: "Skip the tour",
              action: this.endTour,
              secondary: true,
            },
            {
              text: "Next",
              action: this.tour.next,
            },
          ],
        },
        {
          attachTo: {
            element: this.$refs.workspace.$el,
            on: "bottom",
          },
          text: `<img src="${process.env.BASE_URL}images/workspace.gif" class="mx-auto">
            Save individuals in you workspace to compare them or merge them later.`,
          title: "Pin profiles",
          buttons: [
            {
              text: "Skip the tour",
              action: this.endTour,
              secondary: true,
            },
            {
              text: "Next",
              action: this.tour.next,
            },
          ],
        },
        {
          attachTo: {
            element: lockElement,
            on: "right",
          },
          text: `<img src="${process.env.BASE_URL}images/lock.gif" class="mx-auto">
            To prevent any changes in a particular profile, lock it.`,
          title: "Lock profiles to make them read-only",
          buttons: [
            {
              text: "Got it!",
              action: this.endTour,
            },
          ],
        },
      ]);
      this.tour.start();
    },
    endTour() {
      this.$store.dispatch("setTourViewed", true);
      this.tour.complete();
      this.$router.push("/");
    },
    async mockMethod() {
      return true;
    },
    async getIndividuals() {
      return this.individuals;
    },
    async getOrganizations() {
      return this.organizations.data.organizations;
    },
    atChildMounted() {
      this.$forceUpdate();
    },
  },
  mounted() {
    this.$once("hook:updated", function () {
      this.createTour();
    });
  },
  provide() {
    return {
      getRecommendations: this.mockMethod,
      getRecommendationsCount: () => ({
        data: { recommendedMerge: { pageInfo: { totalResults: 0 } } },
      }),
      manageRecommendation: this.mockMethod,
    };
  },
};
</script>
<style lang="scss" scoped>
@import "~shepherd.js/dist/css/shepherd.css";
.row {
  justify-content: space-between;
  margin: 32px;
}
h4 {
  padding: 12px 26px;
}
</style>
