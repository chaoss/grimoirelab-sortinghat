<template>
  <v-main>
    <v-card class="mx-auto elevation-0 mt-3" max-width="800px">
      <v-card-title>
        Search syntax
      </v-card-title>
      <v-card-text>
        <p class="subtitle-2">Search by term</p>
        <p>
          You can find individuals whose identities contain a particular term in
          their name, email address or username by entering the term on the
          search box. You can combine this query with any filters, for example
          <code>John lastUpdated:>2020-11-01</code>.
        </p>
        <p class="subtitle-2">Filter by last updated date</p>
        <p>
          You can filter individuals based on when they were modified, using the
          <code>lastUpdated</code> filter.
        </p>
        <v-simple-table>
          <template v-slot:default>
            <thead>
              <tr>
                <th class="text-left" width="30%">
                  Filter
                </th>
                <th class="text-left">
                  Explanation
                </th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td width="30%"><code>lastUpdated:>YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were updated after the given date.
                </td>
              </tr>
              <tr>
                <td width="30%"><code>lastUpdated:>=YYYY-MM-DD</code></td>
                <td>
                  Matches individuals that were updated on or after the given
                  date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastUpdated:&lt;YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were updated before the given date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastUpdated:&lt;=YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were updated on or before the given
                  date.
                </td>
              </tr>
              <tr>
                <td width="30%">
                  <code>lastUpdated:YYYY-MM-DD..YYYY-MM-DD</code>
                </td>
                <td>
                  Matches individuals that were updated between the given dates.
                </td>
              </tr>
            </tbody>
          </template>
        </v-simple-table>

        <p class="subtitle-2 mt-8">Search for bots</p>
        <p>
          You can search for individuals based on whether they are marked as
          bots, using the <code>isBot:true</code> and <code>isBot:false</code>
          filters.
        </p>
      </v-card-text>
    </v-card>
  </v-main>
</template>

<script>
export default {
  name: "SearchHelp"
};
</script>
