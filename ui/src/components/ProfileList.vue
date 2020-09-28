<template>
  <v-navigation-drawer
    v-model="showDrawer"
    fixed
    right
    width="626"
    min-height="calc(100vh - 66px)"
    color="#eceff1"
    style="top:64px;z-index:1"
  >
    <template v-slot:prepend>
      <v-list-item>
        <v-list-item-content>
          <v-list-item-title>Selected profiles</v-list-item-title>
        </v-list-item-content>
      </v-list-item>
      <v-divider />
    </template>
    <v-row
      v-for="profile in profiles"
      :key="profile.uuid"
      style="padding:10px 0"
    >
      <ProfileCard
        :name="profile.name"
        :enrollments="profile.enrollments"
        :identities="profile.identities"
      />
    </v-row>
  </v-navigation-drawer>
</template>
<script>
import { getProfileByUuid } from "../apollo/queries";
import ProfileCard from "./ProfileCard";
import { mapState } from "vuex";

export default {
  name: "ProfileList",
  components: { ProfileCard },
  data: () => ({
    profiles: []
  }),
  computed: {
    ...mapState(["selectedIndividual"]),
    showDrawer: {
      get() {
        return this.profiles.length >= 1;
      },
      set(newValue) {
        return newValue;
      }
    }
  },
  methods: {
    async addProfile(uuid) {
      const response = await getProfileByUuid(this.$apollo, uuid);
      if (response) {
        const individual = response.data.individuals.entities[0];
        const icons = ["git", "github", "gitlab"];

        const identities = individual.identities.reduce((result, val) => {
          if (icons.find(icon => icon === val.source)) {
            if (result[val.source]) {
              result[val.source].identities.push(val);
            } else {
              result[val.source] = {
                name: val.source,
                identities: [val]
              };
            }
          } else {
            if (result.others) {
              result.others.identities.push(val);
            } else {
              result.others = {
                name: "Others",
                identities: [val]
              };
            }
          }
          return result;
        }, {});
        const formattedProfile = {
          uuid: uuid,
          name: individual.profile.name,
          enrollments: individual.enrollments,
          identities: Object.values(identities)
        };

        this.profiles.push(formattedProfile);
      }
    }
  },
  watch: {
    selectedIndividual(individual) {
      if (individual.selected) {
        this.addProfile(individual.uuid);
      } else {
        const selectedIndex = this.profiles.findIndex(
          profile => profile.uuid === individual.uuid
        );
        this.profiles.splice(selectedIndex, 1);
      }
    }
  }
};
</script>
