# Campaigns

When it comes to Bayesian optimization, campaigns emerge as an essential component.
They encompass a group of interconnected experiments that collectively aim to navigate
the search space and find an optimal solution. They take center stage in orchestrating
the iterative process of selecting, evaluating, and refining candidate solutions.
Thus, campaigns are an integral part of Bayesian optimization and, accordingly,
they also play a central role in BayBE.

The [`Campaign`](baybe.campaign.Campaign) class provides a structured framework for 
defining and documenting an experimentation process.
It further serves as the primary interface for interacting with BayBE as a user
since it is responsible for handling experimental data, making recommendations, adding
measurements, and most other user-related tasks.

## Creating a campaign

### Basic creation

Creating a campaign requires specifying at least two pieces of information that
describe the underlying optimization problem at hand:

| Campaign Specification                     | BayBE Class                                                                               |
|:-------------------------------------------|:------------------------------------------------------------------------------------------|
| What should be optimized in the campaign?  | `Objective` ([class](baybe.objective.Objective) / [user guide](./objective))              |
| Which experimental factors can be altered? | `SearchSpace` ([class](baybe.searchspace.core.SearchSpace) / [user guide](./searchspace)) |

Apart from this basic configuration, it is possible to provide additional instructions, 
such as the specific optimization 
`Strategy`&nbsp;([class](baybe.strategies.base.Strategy) 
/ [user guide](./strategy)) to be used, as well as other aspects of the campaign 
(see [here](#AM) for details on `numerical_measurements_must_be_within_tolerance`).


~~~python
from baybe import Campaign

campaign = Campaign(
    searchspace=searchspace,  # Required
    objective=objective,  # Required
    strategy=strategy,  # Optional
    numerical_measurements_must_be_within_tolerance=boolean,  # Optional
)
~~~

```{attention}
Note that we currently also expose other fields via the constructor. 
This is only temporary, and the corresponding fields should be ignored.
```

### Creation from a JSON config
Instead of using the default constructor, it is also possible to create a `Campaign` 
from a JSON configuration string via 
[`Campaign.from_config`](baybe.campaign.Campaign.from_config).
Herein, the expected JSON schema of the string should mirror the class
hierarchy of the objects nested in the corresponding campaign object.
The string can be easily validated using
[Campaign.validate_config](baybe.campaign.Campaign.validate_config) without
instantiating the object, which skips the potentially costly search space creation step.
For more details and a full exemplary config, we refer to the corresponding
[example](./../../examples/Serialization/create_from_config).

## Getting recommendations

### Basics

```{attention}
Requesting recommendations via `recommend` and adding measurements via
`add_measurements` is the only intended way to interact with a `Campaign` object.
These methods update the necessary metadata that is crucial for the proper execution of
a campaign. We recommend to rely on these methods to maintain the integrity and
reliability of the object.
```

To obtain a recommendation for the next batch of experiments, we can query the 
campaign via the [`recommend`](baybe.campaign.Campaign.recommend) method.
It expects a parameter `batch_quantity` that specifies the desired number of 
experiments to be conducted.

~~~python
rec = campaign.recommend(batch_quantity=3)
print(rec.to_markdown())
~~~

Calling the function returns a `DataFrame` with `batch_quantity` many rows, each
representing a particular parameter configuration from the campaign's search space.
Thus, the following might be a `DataFrame` returned by `recommend` in a search space
with the three parameters `Categorial_1`, `Categorical_2` and `Num_disc_1`:

|    | Categorical_1   | Categorical_2   |   Num_disc_1 |
|---:|:----------------|:----------------|-------------:|
| 15 | B               | good            |            1 |
| 18 | C               | bad             |            1 |
|  9 | B               | bad             |            1 |

```{admonition} Batch optimization
:class: important
In general, the parameter configurations in a recommended batch are **jointly**
optimized and therefore tailored to the specific batch size requested. 
This means that for two batches of different requested sizes, the smaller batch will not 
necessarily correspond to a subset of the configurations contained in the larger batch. 
An intuitive explanation for this phenomenon is that the more experiments one can 
afford to run, the less need there is to focus on "safe bets" and the more room
becomes available to test "high-risk/high-gain" configurations, since only one of the
tested configurations from the batch has to perform well.

**The bottom line is:** You should always ask for exactly as many
recommendations as you are willing to run parallel experiments in your next 
experimental iteration.
An approach where only a subset of experiments taken from a larger recommended batch is
used is strongly discouraged.

**Note:** While the above distinction is true in the general case, it may not be 
relevant for all configured settings, for instance, when the used recommender 
is not capable of joint optimization. Currently, the 
[SequentialGreedyRecommender](baybe.recommenders.bayesian.SequentialGreedyRecommender)
is the only recommender available that performs joint optimization.
```

```{admonition} Sequential vs. parallel experimentation
:class: note
If you have a fixed experimental budget but the luxury of choosing 
whether to run your experiments sequentially or in parallel, sequential 
experimentation will give you the better overall results in expectation.
This is because in the sequential approach, each subsequent recommendation can 
leverage the additional data from previous iterations, which allows 
more accurate predictive models to be built. However, in real-world use cases, the 
question is typically answered by other factors, such as whether parallel
experimentation is feasible in the first place, or whether the given time budget 
even allows for sequential runs.
```

### Caching of recommendations

The `Campaign` object caches the last batch of recommendations returned, in order to 
avoid unnecessary computations for subsequent queries between which the status
of the campaign has not changed. 
The cache is invalidated as soon as new measurements are added or a different
batch size is desired.
The latter is necessary because each batch is optimized for the specific number of 
experiments requested (see note above).

(AM)=
## Adding measurements

Available experimental data can be added at any time during the campaign lifecycle using
the [`add_measurements`](baybe.campaign.Campaign.add_measurements) method, 
which expects a `DataFrame` containing the values of the used experimental parameters
and all corresponding target measurements.
If measurements are to be added immediately after a call to `recommend`,
this is most easily achieved by augmenting the  `DataFrame` returned from that call 
with the respective target columns.

~~~python
rec["Target_max"] = [2, 4, 9]  # 3 values matching the batch_quantity of 3
campaign.add_measurements(rec)
new_rec = campaign.recommend(batch_quantity=5)
~~~

After adding the measurements, the corresponding `DataFrame` thus has the following 
form:

|    | Categorical_1   | Categorical_2   |   Num_disc_1 |   Target_max |
|---:|:----------------|:----------------|-------------:|-------------:|
| 15 | B               | good            |            1 |            2 |
| 18 | C               | bad             |            1 |            4 |
|  9 | B               | bad             |            1 |            9 |

```{admonition} Parameter tolerances
:class: note
For discrete parameters, the parameter values associated with the provided measurements
are required to fall into a predefined tolerance interval by default, which is
defined on the level of the individual parameters.
This requirement can be disabled using the 
`numerical_measurements_must_be_within_tolerance` flag of the campaign.
```


## Serialization

Like most of the objects managed by BayBE, `Campaign` objects can be serialized and
deserialized using the [`to_json`](baybe.utils.serialization.SerialMixin.to_json) and
[`from_json`](baybe.utils.serialization.SerialMixin.from_json) methods, which 
allow to convert between Python objects their corresponding representation in JSON 
format. 
These representations are fully equivalent, meaning that serializing and subsequently 
deserializing a campaign yields an exact copy of the object:

~~~python
campaign_json = campaign.to_json()
recreated_campaign = Campaign.from_json(campaign_json)
assert campaign == recreated_campaign
~~~

This provides an easy way to persist the current state of your campaign for long 
term storage and continue the experimentation at a later point in time.
For more information on serialization, we
refer to the corresponding [examples](./../../examples/Serialization/Serialization).

```{admonition} Dataframe serialization
:class: note
Note that `DataFrame` objects associated with the `Campaign` object are converted to 
a binary format during serialization, which has the consequence that their JSON 
representation is not human-readable.
```

## Further information

Campaigns are created as a first step in most of our 
[examples](./../../examples/examples).
For more details on how to define campaigns for a specific use case, we thus propose 
to have a look at the most suitable example.
