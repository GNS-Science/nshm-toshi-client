import sgqlc.types
import sgqlc.types.datetime
import sgqlc.types.relay


schema = sgqlc.types.Schema()


# Unexport Node/PageInfo, let schema re-declare them
schema -= sgqlc.types.relay.Node
schema -= sgqlc.types.relay.PageInfo



########################################################################
# Scalars and Enumerations
########################################################################
class AggregationFn(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('MEAN',)


class BigInt(sgqlc.types.Scalar):
    __schema__ = schema


Boolean = sgqlc.types.Boolean

DateTime = sgqlc.types.datetime.DateTime

class EventResult(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('FAILURE', 'PARTIAL', 'SUCCESS', 'UNDEFINED')


class EventState(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('DONE', 'SCHEDULED', 'STARTED', 'UNDEFINED')


class FileRole(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('READ', 'READ_WRITE', 'UNDEFINED', 'WRITE')


Float = sgqlc.types.Float

ID = sgqlc.types.ID

Int = sgqlc.types.Int

class ModelType(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('COMPOSITE', 'CRUSTAL', 'SUBDUCTION')


class OpenquakeTaskType(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('DISAGG', 'HAZARD', 'UNDEFINED')


class RowItemType(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('boolean', 'double', 'integer', 'string')


class SmsFileType(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('BH', 'CPT', 'DH', 'HVSR', 'SW')


class SmsSiteClass(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('A', 'B', 'C', 'D', 'E')


class SmsSiteClassBasis(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('SPT', 'Vs', 'su')


String = sgqlc.types.String

class TableType(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('GENERAL', 'HAZARD_GRIDDED', 'HAZARD_SITES', 'MFD_CURVES', 'MFD_CURVES_V2')


class TaskSubType(sgqlc.types.Enum):
    __schema__ = schema
    __choices__ = ('AGGREGATE_SOLUTION', 'HAZARD', 'INVERSION', 'OPENQUAKE_HAZARD', 'REPORT', 'RUPTURE_SET', 'SCALE_SOLUTION', 'SOLUTION_TO_NRML', 'TIME_DEPENDENT_SOLUTION')



########################################################################
# Input Objects
########################################################################
class AppendInversionSolutionTablesInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('id', 'tables', 'client_mutation_id')
    id = sgqlc.types.Field(ID, graphql_name='id')
    tables = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('LabelledTableRelationInput')), graphql_name='tables')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class AutomationTaskInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('result', 'state', 'created', 'duration', 'arguments', 'environment', 'metrics')
    result = sgqlc.types.Field(sgqlc.types.non_null(EventResult), graphql_name='result')
    state = sgqlc.types.Field(sgqlc.types.non_null(EventState), graphql_name='state')
    created = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='created')
    duration = sgqlc.types.Field(Float, graphql_name='duration')
    arguments = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='arguments')
    environment = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='environment')
    metrics = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='metrics')


class AutomationTaskUpdateInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('task_id', 'result', 'state', 'duration', 'arguments', 'environment', 'metrics')
    task_id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='task_id')
    result = sgqlc.types.Field(EventResult, graphql_name='result')
    state = sgqlc.types.Field(EventState, graphql_name='state')
    duration = sgqlc.types.Field(Float, graphql_name='duration')
    arguments = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='arguments')
    environment = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='environment')
    metrics = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='metrics')


class CreateAggregateInversionSolutionInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('file_name', 'md5_digest', 'file_size', 'meta', 'common_rupture_set', 'source_solutions', 'aggregation_fn', 'produced_by', 'created', 'predecessors', 'client_mutation_id')
    file_name = sgqlc.types.Field(String, graphql_name='file_name')
    md5_digest = sgqlc.types.Field(String, graphql_name='md5_digest')
    file_size = sgqlc.types.Field(BigInt, graphql_name='file_size')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    common_rupture_set = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='common_rupture_set')
    source_solutions = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of(ID)), graphql_name='source_solutions')
    aggregation_fn = sgqlc.types.Field(sgqlc.types.non_null(AggregationFn), graphql_name='aggregation_fn')
    produced_by = sgqlc.types.Field(ID, graphql_name='produced_by')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    predecessors = sgqlc.types.Field(sgqlc.types.list_of('PredecessorInput'), graphql_name='predecessors')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateGeneralTaskInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('notes', 'subtask_count', 'subtask_type', 'model_type', 'subtask_result', 'created', 'agent_name', 'title', 'description', 'argument_lists', 'meta', 'client_mutation_id')
    notes = sgqlc.types.Field(String, graphql_name='notes')
    subtask_count = sgqlc.types.Field(Int, graphql_name='subtask_count')
    subtask_type = sgqlc.types.Field(TaskSubType, graphql_name='subtask_type')
    model_type = sgqlc.types.Field(ModelType, graphql_name='model_type')
    subtask_result = sgqlc.types.Field(EventResult, graphql_name='subtask_result')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    agent_name = sgqlc.types.Field(String, graphql_name='agent_name')
    title = sgqlc.types.Field(String, graphql_name='title')
    description = sgqlc.types.Field(String, graphql_name='description')
    argument_lists = sgqlc.types.Field(sgqlc.types.list_of('KeyValueListPairInput'), graphql_name='argument_lists')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateInversionSolutionInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('file_name', 'md5_digest', 'file_size', 'meta', 'created', 'mfd_table_id', 'hazard_table_id', 'produced_by', 'predecessors', 'tables', 'metrics', 'client_mutation_id')
    file_name = sgqlc.types.Field(String, graphql_name='file_name')
    md5_digest = sgqlc.types.Field(String, graphql_name='md5_digest')
    file_size = sgqlc.types.Field(BigInt, graphql_name='file_size')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    mfd_table_id = sgqlc.types.Field(ID, graphql_name='mfd_table_id')
    hazard_table_id = sgqlc.types.Field(ID, graphql_name='hazard_table_id')
    produced_by = sgqlc.types.Field(ID, graphql_name='produced_by')
    predecessors = sgqlc.types.Field(sgqlc.types.list_of('PredecessorInput'), graphql_name='predecessors')
    tables = sgqlc.types.Field(sgqlc.types.list_of('LabelledTableRelationInput'), graphql_name='tables')
    metrics = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='metrics')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateInversionSolutionNrmlInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('file_name', 'md5_digest', 'file_size', 'meta', 'created', 'source_solution', 'predecessors', 'client_mutation_id')
    file_name = sgqlc.types.Field(String, graphql_name='file_name')
    md5_digest = sgqlc.types.Field(String, graphql_name='md5_digest')
    file_size = sgqlc.types.Field(BigInt, graphql_name='file_size')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    source_solution = sgqlc.types.Field(ID, graphql_name='source_solution')
    predecessors = sgqlc.types.Field(sgqlc.types.list_of('PredecessorInput'), graphql_name='predecessors')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateOpenquakeHazardConfigInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('created', 'source_models', 'template_archive', 'client_mutation_id')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    source_models = sgqlc.types.Field(sgqlc.types.list_of(ID), graphql_name='source_models')
    template_archive = sgqlc.types.Field(ID, graphql_name='template_archive')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateOpenquakeHazardSolutionInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('created', 'config', 'produced_by', 'csv_archive', 'hdf5_archive', 'modified_config', 'task_args', 'meta', 'metrics', 'predecessors', 'client_mutation_id')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    config = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='config')
    produced_by = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='produced_by')
    csv_archive = sgqlc.types.Field(ID, graphql_name='csv_archive')
    hdf5_archive = sgqlc.types.Field(ID, graphql_name='hdf5_archive')
    modified_config = sgqlc.types.Field(ID, graphql_name='modified_config')
    task_args = sgqlc.types.Field(ID, graphql_name='task_args')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    metrics = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='metrics')
    predecessors = sgqlc.types.Field(sgqlc.types.list_of('PredecessorInput'), graphql_name='predecessors')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateScaledInversionSolutionInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('file_name', 'md5_digest', 'file_size', 'meta', 'source_solution', 'produced_by', 'created', 'predecessors', 'client_mutation_id')
    file_name = sgqlc.types.Field(String, graphql_name='file_name')
    md5_digest = sgqlc.types.Field(String, graphql_name='md5_digest')
    file_size = sgqlc.types.Field(BigInt, graphql_name='file_size')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    source_solution = sgqlc.types.Field(ID, graphql_name='source_solution')
    produced_by = sgqlc.types.Field(ID, graphql_name='produced_by')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    predecessors = sgqlc.types.Field(sgqlc.types.list_of('PredecessorInput'), graphql_name='predecessors')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateStrongMotionStationInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('created', 'updated', 'site_code', 'site_class', 'site_class_basis', 'vs30_mean', 'vs30_std_dev', 'bedrock_encountered', 'liquefiable', 'soft_clay_or_peat', 'client_mutation_id')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    updated = sgqlc.types.Field(DateTime, graphql_name='updated')
    site_code = sgqlc.types.Field(String, graphql_name='site_code')
    site_class = sgqlc.types.Field(SmsSiteClass, graphql_name='site_class')
    site_class_basis = sgqlc.types.Field(SmsSiteClassBasis, graphql_name='site_class_basis')
    vs30_mean = sgqlc.types.Field(sgqlc.types.list_of(Float), graphql_name='Vs30_mean')
    vs30_std_dev = sgqlc.types.Field(sgqlc.types.list_of(Float), graphql_name='Vs30_std_dev')
    bedrock_encountered = sgqlc.types.Field(Boolean, graphql_name='bedrock_encountered')
    liquefiable = sgqlc.types.Field(Boolean, graphql_name='liquefiable')
    soft_clay_or_peat = sgqlc.types.Field(Boolean, graphql_name='soft_clay_or_peat')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateTableInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('name', 'object_id', 'created', 'column_headers', 'column_types', 'rows', 'meta', 'table_type', 'dimensions', 'client_mutation_id')
    name = sgqlc.types.Field(String, graphql_name='name')
    object_id = sgqlc.types.Field(ID, graphql_name='object_id')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    column_headers = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='column_headers')
    column_types = sgqlc.types.Field(sgqlc.types.list_of(RowItemType), graphql_name='column_types')
    rows = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.list_of(String)), graphql_name='rows')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    table_type = sgqlc.types.Field(sgqlc.types.non_null(TableType), graphql_name='table_type')
    dimensions = sgqlc.types.Field(sgqlc.types.list_of('KeyValueListPairInput'), graphql_name='dimensions')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateTimeDependentInversionSolutionInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('file_name', 'md5_digest', 'file_size', 'meta', 'source_solution', 'produced_by', 'created', 'predecessors', 'client_mutation_id')
    file_name = sgqlc.types.Field(String, graphql_name='file_name')
    md5_digest = sgqlc.types.Field(String, graphql_name='md5_digest')
    file_size = sgqlc.types.Field(BigInt, graphql_name='file_size')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePairInput'), graphql_name='meta')
    source_solution = sgqlc.types.Field(ID, graphql_name='source_solution')
    produced_by = sgqlc.types.Field(ID, graphql_name='produced_by')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    predecessors = sgqlc.types.Field(sgqlc.types.list_of('PredecessorInput'), graphql_name='predecessors')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class KeyValueListPairInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('k', 'v')
    k = sgqlc.types.Field(String, graphql_name='k')
    v = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='v')


class KeyValuePairInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('k', 'v')
    k = sgqlc.types.Field(String, graphql_name='k')
    v = sgqlc.types.Field(String, graphql_name='v')


class LabelledTableRelationInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('produced_by_id', 'label', 'table_id', 'table_type', 'dimensions')
    produced_by_id = sgqlc.types.Field(ID, graphql_name='produced_by_id')
    label = sgqlc.types.Field(String, graphql_name='label')
    table_id = sgqlc.types.Field(ID, graphql_name='table_id')
    table_type = sgqlc.types.Field(TableType, graphql_name='table_type')
    dimensions = sgqlc.types.Field(sgqlc.types.list_of(KeyValueListPairInput), graphql_name='dimensions')


class NewAutomationTaskInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('result', 'state', 'created', 'duration', 'arguments', 'environment', 'metrics', 'model_type', 'task_type')
    result = sgqlc.types.Field(sgqlc.types.non_null(EventResult), graphql_name='result')
    state = sgqlc.types.Field(sgqlc.types.non_null(EventState), graphql_name='state')
    created = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='created')
    duration = sgqlc.types.Field(Float, graphql_name='duration')
    arguments = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='arguments')
    environment = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='environment')
    metrics = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='metrics')
    model_type = sgqlc.types.Field(ModelType, graphql_name='model_type')
    task_type = sgqlc.types.Field(sgqlc.types.non_null(TaskSubType), graphql_name='task_type')


class OpenquakeHazardTaskInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('result', 'state', 'created', 'duration', 'arguments', 'environment', 'metrics', 'config', 'model_type', 'task_type')
    result = sgqlc.types.Field(sgqlc.types.non_null(EventResult), graphql_name='result')
    state = sgqlc.types.Field(sgqlc.types.non_null(EventState), graphql_name='state')
    created = sgqlc.types.Field(sgqlc.types.non_null(DateTime), graphql_name='created')
    duration = sgqlc.types.Field(Float, graphql_name='duration')
    arguments = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='arguments')
    environment = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='environment')
    metrics = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='metrics')
    config = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='config')
    model_type = sgqlc.types.Field(sgqlc.types.non_null(ModelType), graphql_name='model_type')
    task_type = sgqlc.types.Field(OpenquakeTaskType, graphql_name='task_type')


class OpenquakeHazardTaskUpdateInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('task_id', 'result', 'state', 'duration', 'arguments', 'environment', 'metrics', 'hazard_solution')
    task_id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='task_id')
    result = sgqlc.types.Field(EventResult, graphql_name='result')
    state = sgqlc.types.Field(EventState, graphql_name='state')
    duration = sgqlc.types.Field(Float, graphql_name='duration')
    arguments = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='arguments')
    environment = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='environment')
    metrics = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='metrics')
    hazard_solution = sgqlc.types.Field(ID, graphql_name='hazard_solution')


class PredecessorInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('id', 'depth')
    id = sgqlc.types.Field(ID, graphql_name='id')
    depth = sgqlc.types.Field(Int, graphql_name='depth')


class UpdateGeneralTaskInput(sgqlc.types.Input):
    __schema__ = schema
    __field_names__ = ('created', 'updated', 'agent_name', 'title', 'description', 'notes', 'subtask_count', 'subtask_type', 'model_type', 'subtask_result', 'task_id', 'argument_lists', 'meta', 'client_mutation_id')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    updated = sgqlc.types.Field(DateTime, graphql_name='updated')
    agent_name = sgqlc.types.Field(String, graphql_name='agent_name')
    title = sgqlc.types.Field(String, graphql_name='title')
    description = sgqlc.types.Field(String, graphql_name='description')
    notes = sgqlc.types.Field(String, graphql_name='notes')
    subtask_count = sgqlc.types.Field(Int, graphql_name='subtask_count')
    subtask_type = sgqlc.types.Field(TaskSubType, graphql_name='subtask_type')
    model_type = sgqlc.types.Field(ModelType, graphql_name='model_type')
    subtask_result = sgqlc.types.Field(EventResult, graphql_name='subtask_result')
    task_id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='task_id')
    argument_lists = sgqlc.types.Field(sgqlc.types.list_of(KeyValueListPairInput), graphql_name='argument_lists')
    meta = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePairInput), graphql_name='meta')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')



########################################################################
# Output Objects and Interfaces
########################################################################
class AutomationTaskInterface(sgqlc.types.Interface):
    __schema__ = schema
    __field_names__ = ('result', 'state', 'created', 'duration', 'parents', 'arguments', 'environment', 'metrics')
    result = sgqlc.types.Field(EventResult, graphql_name='result')
    state = sgqlc.types.Field(EventState, graphql_name='state')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    duration = sgqlc.types.Field(Float, graphql_name='duration')
    parents = sgqlc.types.Field('TaskTaskRelationConnection', graphql_name='parents', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    arguments = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePair'), graphql_name='arguments')
    environment = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePair'), graphql_name='environment')
    metrics = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePair'), graphql_name='metrics')


class FileInterface(sgqlc.types.Interface):
    __schema__ = schema
    __field_names__ = ('file_name', 'md5_digest', 'file_size', 'file_url', 'post_url', 'meta', 'relations')
    file_name = sgqlc.types.Field(String, graphql_name='file_name')
    md5_digest = sgqlc.types.Field(String, graphql_name='md5_digest')
    file_size = sgqlc.types.Field(BigInt, graphql_name='file_size')
    file_url = sgqlc.types.Field(String, graphql_name='file_url')
    post_url = sgqlc.types.Field(String, graphql_name='post_url')
    meta = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePair'), graphql_name='meta')
    relations = sgqlc.types.Field('FileRelationConnection', graphql_name='relations', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )


class InversionSolutionInterface(sgqlc.types.Interface):
    __schema__ = schema
    __field_names__ = ('created', 'metrics', 'mfd_table_id', 'hazard_table_id', 'hazard_table', 'mfd_table', 'produced_by', 'tables')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    metrics = sgqlc.types.Field(sgqlc.types.list_of('KeyValuePair'), graphql_name='metrics')
    mfd_table_id = sgqlc.types.Field(ID, graphql_name='mfd_table_id')
    hazard_table_id = sgqlc.types.Field(ID, graphql_name='hazard_table_id')
    hazard_table = sgqlc.types.Field('Table', graphql_name='hazard_table')
    mfd_table = sgqlc.types.Field('Table', graphql_name='mfd_table')
    produced_by = sgqlc.types.Field('AutomationTaskUnion', graphql_name='produced_by')
    tables = sgqlc.types.Field(sgqlc.types.list_of('LabelledTableRelation'), graphql_name='tables')


class Node(sgqlc.types.Interface):
    __schema__ = schema
    __field_names__ = ('id',)
    id = sgqlc.types.Field(sgqlc.types.non_null(ID), graphql_name='id')


class PredecessorsInterface(sgqlc.types.Interface):
    __schema__ = schema
    __field_names__ = ('predecessors',)
    predecessors = sgqlc.types.Field(sgqlc.types.list_of('Predecessor'), graphql_name='predecessors')


class Thing(sgqlc.types.Interface):
    __schema__ = schema
    __field_names__ = ('created', 'files', 'parents', 'children')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    files = sgqlc.types.Field('FileRelationConnection', graphql_name='files', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    parents = sgqlc.types.Field('TaskTaskRelationConnection', graphql_name='parents', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    children = sgqlc.types.Field('TaskTaskRelationConnection', graphql_name='children', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )


class AppendInversionSolutionTablesPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('inversion_solution', 'ok', 'client_mutation_id')
    inversion_solution = sgqlc.types.Field('InversionSolution', graphql_name='inversion_solution')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateAggregateInversionSolutionPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('solution', 'ok', 'client_mutation_id')
    solution = sgqlc.types.Field('AggregateInversionSolution', graphql_name='solution')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateAutomationTask(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('task_result',)
    task_result = sgqlc.types.Field('AutomationTask', graphql_name='task_result')


class CreateFile(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'file_result')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    file_result = sgqlc.types.Field('File', graphql_name='file_result')


class CreateFileRelation(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'file_relation')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    file_relation = sgqlc.types.Field('FileRelation', graphql_name='file_relation')


class CreateGeneralTaskPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('general_task', 'client_mutation_id')
    general_task = sgqlc.types.Field('GeneralTask', graphql_name='general_task')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateInversionSolutionNrmlPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('inversion_solution_nrml', 'ok', 'client_mutation_id')
    inversion_solution_nrml = sgqlc.types.Field('InversionSolutionNrml', graphql_name='inversion_solution_nrml')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateInversionSolutionPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('inversion_solution', 'ok', 'client_mutation_id')
    inversion_solution = sgqlc.types.Field('InversionSolution', graphql_name='inversion_solution')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateOpenquakeHazardConfigPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('config', 'ok', 'client_mutation_id')
    config = sgqlc.types.Field('OpenquakeHazardConfig', graphql_name='config')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateOpenquakeHazardSolutionPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('openquake_hazard_solution', 'ok', 'client_mutation_id')
    openquake_hazard_solution = sgqlc.types.Field('OpenquakeHazardSolution', graphql_name='openquake_hazard_solution')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateOpenquakeHazardTask(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'openquake_hazard_task')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    openquake_hazard_task = sgqlc.types.Field('OpenquakeHazardTask', graphql_name='openquake_hazard_task')


class CreateRuptureGenerationTask(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('task_result',)
    task_result = sgqlc.types.Field('RuptureGenerationTask', graphql_name='task_result')


class CreateScaledInversionSolutionPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('solution', 'ok', 'client_mutation_id')
    solution = sgqlc.types.Field('ScaledInversionSolution', graphql_name='solution')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateSmsFile(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'file_result')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    file_result = sgqlc.types.Field('SmsFile', graphql_name='file_result')


class CreateStrongMotionStationPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('strong_motion_station', 'client_mutation_id')
    strong_motion_station = sgqlc.types.Field('StrongMotionStation', graphql_name='strong_motion_station')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateTablePayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('table', 'client_mutation_id')
    table = sgqlc.types.Field('Table', graphql_name='table')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class CreateTaskTaskRelation(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'thing_relation')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    thing_relation = sgqlc.types.Field('TaskTaskRelation', graphql_name='thing_relation')


class CreateTimeDependentInversionSolutionPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('solution', 'ok', 'client_mutation_id')
    solution = sgqlc.types.Field('TimeDependentInversionSolution', graphql_name='solution')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class FileConnection(sgqlc.types.relay.Connection):
    __schema__ = schema
    __field_names__ = ('page_info', 'edges', 'total_count')
    page_info = sgqlc.types.Field(sgqlc.types.non_null('PageInfo'), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('FileEdge')), graphql_name='edges')
    total_count = sgqlc.types.Field(Int, graphql_name='total_count')


class FileEdge(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field('File', graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class FileRelation(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('thing', 'file', 'role', 'thing_id', 'file_id')
    thing = sgqlc.types.Field(Thing, graphql_name='thing')
    file = sgqlc.types.Field('FileUnion', graphql_name='file')
    role = sgqlc.types.Field(sgqlc.types.non_null(FileRole), graphql_name='role')
    thing_id = sgqlc.types.Field(String, graphql_name='thing_id')
    file_id = sgqlc.types.Field(String, graphql_name='file_id')


class FileRelationConnection(sgqlc.types.relay.Connection):
    __schema__ = schema
    __field_names__ = ('page_info', 'edges', 'total_count')
    page_info = sgqlc.types.Field(sgqlc.types.non_null('PageInfo'), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('FileRelationEdge')), graphql_name='edges')
    total_count = sgqlc.types.Field(Int, graphql_name='total_count')


class FileRelationEdge(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field(FileRelation, graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class KeyValueListPair(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('k', 'v')
    k = sgqlc.types.Field(String, graphql_name='k')
    v = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='v')


class KeyValuePair(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('k', 'v')
    k = sgqlc.types.Field(String, graphql_name='k')
    v = sgqlc.types.Field(String, graphql_name='v')


class LabelledTableRelation(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('identity', 'created', 'produced_by_id', 'label', 'table_id', 'table', 'table_type', 'dimensions')
    identity = sgqlc.types.Field(String, graphql_name='identity')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    produced_by_id = sgqlc.types.Field(ID, graphql_name='produced_by_id')
    label = sgqlc.types.Field(String, graphql_name='label')
    table_id = sgqlc.types.Field(ID, graphql_name='table_id')
    table = sgqlc.types.Field('Table', graphql_name='table')
    table_type = sgqlc.types.Field(TableType, graphql_name='table_type')
    dimensions = sgqlc.types.Field(sgqlc.types.list_of(KeyValueListPair), graphql_name='dimensions')


class MutationRoot(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('append_inversion_solution_tables', 'create_automation_task', 'create_file', 'create_file_relation', 'create_general_task', 'create_inversion_solution', 'create_rupture_generation_task', 'create_sms_file', 'create_strong_motion_station', 'create_table', 'create_task_relation', 'update_automation_task', 'update_general_task', 'update_rupture_generation_task', 'create_aggregate_inversion_solution', 'create_scaled_inversion_solution', 'create_time_dependent_inversion_solution', 'create_inversion_solution_nrml', 'create_openquake_hazard_solution', 'create_openquake_hazard_config', 'create_openquake_hazard_task', 'update_openquake_hazard_task')
    append_inversion_solution_tables = sgqlc.types.Field(AppendInversionSolutionTablesPayload, graphql_name='append_inversion_solution_tables', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(AppendInversionSolutionTablesInput), graphql_name='input', default=None)),
))
    )
    create_automation_task = sgqlc.types.Field(CreateAutomationTask, graphql_name='create_automation_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(NewAutomationTaskInput), graphql_name='input', default=None)),
))
    )
    create_file = sgqlc.types.Field(CreateFile, graphql_name='create_file', args=sgqlc.types.ArgDict((
        ('file_name', sgqlc.types.Arg(String, graphql_name='file_name', default=None)),
        ('file_size', sgqlc.types.Arg(BigInt, graphql_name='file_size', default=None)),
        ('md5_digest', sgqlc.types.Arg(String, graphql_name='md5_digest', default='The base64-encoded md5 digest of the file')),
        ('meta', sgqlc.types.Arg(sgqlc.types.list_of(KeyValuePairInput), graphql_name='meta', default=None)),
        ('predecessors', sgqlc.types.Arg(sgqlc.types.list_of(PredecessorInput), graphql_name='predecessors', default=None)),
))
    )
    create_file_relation = sgqlc.types.Field(CreateFileRelation, graphql_name='create_file_relation', args=sgqlc.types.ArgDict((
        ('file_id', sgqlc.types.Arg(sgqlc.types.non_null(ID), graphql_name='file_id', default=None)),
        ('role', sgqlc.types.Arg(sgqlc.types.non_null(FileRole), graphql_name='role', default=None)),
        ('thing_id', sgqlc.types.Arg(sgqlc.types.non_null(ID), graphql_name='thing_id', default=None)),
))
    )
    create_general_task = sgqlc.types.Field(CreateGeneralTaskPayload, graphql_name='create_general_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateGeneralTaskInput), graphql_name='input', default=None)),
))
    )
    create_inversion_solution = sgqlc.types.Field(CreateInversionSolutionPayload, graphql_name='create_inversion_solution', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateInversionSolutionInput), graphql_name='input', default=None)),
))
    )
    create_rupture_generation_task = sgqlc.types.Field(CreateRuptureGenerationTask, graphql_name='create_rupture_generation_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(AutomationTaskInput), graphql_name='input', default=None)),
))
    )
    create_sms_file = sgqlc.types.Field(CreateSmsFile, graphql_name='create_sms_file', args=sgqlc.types.ArgDict((
        ('file_name', sgqlc.types.Arg(String, graphql_name='file_name', default=None)),
        ('file_size', sgqlc.types.Arg(BigInt, graphql_name='file_size', default=None)),
        ('file_type', sgqlc.types.Arg(sgqlc.types.non_null(SmsFileType), graphql_name='file_type', default=None)),
        ('md5_digest', sgqlc.types.Arg(String, graphql_name='md5_digest', default='The base64-encoded md5 digest of the file')),
))
    )
    create_strong_motion_station = sgqlc.types.Field(CreateStrongMotionStationPayload, graphql_name='create_strong_motion_station', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateStrongMotionStationInput), graphql_name='input', default=None)),
))
    )
    create_table = sgqlc.types.Field(CreateTablePayload, graphql_name='create_table', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateTableInput), graphql_name='input', default=None)),
))
    )
    create_task_relation = sgqlc.types.Field(CreateTaskTaskRelation, graphql_name='create_task_relation', args=sgqlc.types.ArgDict((
        ('child_id', sgqlc.types.Arg(sgqlc.types.non_null(ID), graphql_name='child_id', default=None)),
        ('parent_id', sgqlc.types.Arg(sgqlc.types.non_null(ID), graphql_name='parent_id', default=None)),
))
    )
    update_automation_task = sgqlc.types.Field('UpdateAutomationTask', graphql_name='update_automation_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(AutomationTaskUpdateInput), graphql_name='input', default=None)),
))
    )
    update_general_task = sgqlc.types.Field('UpdateGeneralTaskPayload', graphql_name='update_general_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(UpdateGeneralTaskInput), graphql_name='input', default=None)),
))
    )
    update_rupture_generation_task = sgqlc.types.Field('UpdateRuptureGenerationTask', graphql_name='update_rupture_generation_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(AutomationTaskUpdateInput), graphql_name='input', default=None)),
))
    )
    create_aggregate_inversion_solution = sgqlc.types.Field(CreateAggregateInversionSolutionPayload, graphql_name='create_aggregate_inversion_solution', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateAggregateInversionSolutionInput), graphql_name='input', default=None)),
))
    )
    create_scaled_inversion_solution = sgqlc.types.Field(CreateScaledInversionSolutionPayload, graphql_name='create_scaled_inversion_solution', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateScaledInversionSolutionInput), graphql_name='input', default=None)),
))
    )
    create_time_dependent_inversion_solution = sgqlc.types.Field(CreateTimeDependentInversionSolutionPayload, graphql_name='create_time_dependent_inversion_solution', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateTimeDependentInversionSolutionInput), graphql_name='input', default=None)),
))
    )
    create_inversion_solution_nrml = sgqlc.types.Field(CreateInversionSolutionNrmlPayload, graphql_name='create_inversion_solution_nrml', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateInversionSolutionNrmlInput), graphql_name='input', default=None)),
))
    )
    create_openquake_hazard_solution = sgqlc.types.Field(CreateOpenquakeHazardSolutionPayload, graphql_name='create_openquake_hazard_solution', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateOpenquakeHazardSolutionInput), graphql_name='input', default=None)),
))
    )
    create_openquake_hazard_config = sgqlc.types.Field(CreateOpenquakeHazardConfigPayload, graphql_name='create_openquake_hazard_config', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(CreateOpenquakeHazardConfigInput), graphql_name='input', default=None)),
))
    )
    create_openquake_hazard_task = sgqlc.types.Field(CreateOpenquakeHazardTask, graphql_name='create_openquake_hazard_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(sgqlc.types.non_null(OpenquakeHazardTaskInput), graphql_name='input', default=None)),
))
    )
    update_openquake_hazard_task = sgqlc.types.Field('UpdateOpenquakeHazardTask', graphql_name='update_openquake_hazard_task', args=sgqlc.types.ArgDict((
        ('input', sgqlc.types.Arg(OpenquakeHazardTaskUpdateInput, graphql_name='input', default=None)),
))
    )


class NodeFilter(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'result')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    result = sgqlc.types.Field('SearchResultConnection', graphql_name='result', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )


class ObjectIdentitiesConnection(sgqlc.types.relay.Connection):
    __schema__ = schema
    __field_names__ = ('page_info', 'edges')
    page_info = sgqlc.types.Field(sgqlc.types.non_null('PageInfo'), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('ObjectIdentitiesEdge')), graphql_name='edges')


class ObjectIdentitiesEdge(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field('ObjectIdentity', graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class PageInfo(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('has_next_page', 'has_previous_page', 'start_cursor', 'end_cursor')
    has_next_page = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='hasNextPage')
    has_previous_page = sgqlc.types.Field(sgqlc.types.non_null(Boolean), graphql_name='hasPreviousPage')
    start_cursor = sgqlc.types.Field(String, graphql_name='startCursor')
    end_cursor = sgqlc.types.Field(String, graphql_name='endCursor')


class Predecessor(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('id', 'typename', 'depth', 'relationship', 'node')
    id = sgqlc.types.Field(ID, graphql_name='id')
    typename = sgqlc.types.Field(String, graphql_name='typename')
    depth = sgqlc.types.Field(Int, graphql_name='depth')
    relationship = sgqlc.types.Field(String, graphql_name='relationship')
    node = sgqlc.types.Field('PredecessorUnion', graphql_name='node')


class QueryRoot(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('about', 'version', 'rupture_generation_tasks', 'files', 'node', 'nodes', 'reindex', 'search', 'object_identities', 'legacy_object_identities', 'strong_motion_station', 'strong_motion_stations')
    about = sgqlc.types.Field(String, graphql_name='about')
    version = sgqlc.types.Field(String, graphql_name='version')
    rupture_generation_tasks = sgqlc.types.Field('RuptureGenerationTaskConnection', graphql_name='rupture_generation_tasks', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    files = sgqlc.types.Field(FileConnection, graphql_name='files', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    node = sgqlc.types.Field(Node, graphql_name='node', args=sgqlc.types.ArgDict((
        ('id', sgqlc.types.Arg(sgqlc.types.non_null(ID), graphql_name='id', default=None)),
))
    )
    nodes = sgqlc.types.Field(NodeFilter, graphql_name='nodes', args=sgqlc.types.ArgDict((
        ('id_in', sgqlc.types.Arg(sgqlc.types.list_of(ID), graphql_name='id_in', default=None)),
))
    )
    reindex = sgqlc.types.Field(NodeFilter, graphql_name='reindex', args=sgqlc.types.ArgDict((
        ('id_in', sgqlc.types.Arg(sgqlc.types.list_of(ID), graphql_name='id_in', default=None)),
))
    )
    search = sgqlc.types.Field('Search', graphql_name='search', args=sgqlc.types.ArgDict((
        ('search_term', sgqlc.types.Arg(String, graphql_name='search_term', default=None)),
))
    )
    object_identities = sgqlc.types.Field(ObjectIdentitiesConnection, graphql_name='object_identities', args=sgqlc.types.ArgDict((
        ('object_type', sgqlc.types.Arg(String, graphql_name='object_type', default=None)),
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    legacy_object_identities = sgqlc.types.Field(ObjectIdentitiesConnection, graphql_name='legacy_object_identities', args=sgqlc.types.ArgDict((
        ('store_type', sgqlc.types.Arg(String, graphql_name='store_type', default=None)),
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )
    strong_motion_station = sgqlc.types.Field('StrongMotionStation', graphql_name='strong_motion_station', args=sgqlc.types.ArgDict((
        ('id', sgqlc.types.Arg(sgqlc.types.non_null(ID), graphql_name='id', default=None)),
))
    )
    strong_motion_stations = sgqlc.types.Field('StrongMotionStationConnection', graphql_name='strong_motion_stations', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )


class RuptureGenerationTaskConnection(sgqlc.types.relay.Connection):
    __schema__ = schema
    __field_names__ = ('page_info', 'edges', 'total_count')
    page_info = sgqlc.types.Field(sgqlc.types.non_null(PageInfo), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('RuptureGenerationTaskEdge')), graphql_name='edges')
    total_count = sgqlc.types.Field(Int, graphql_name='total_count')


class RuptureGenerationTaskEdge(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field('RuptureGenerationTask', graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class Search(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'search_result')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    search_result = sgqlc.types.Field('SearchResultConnection', graphql_name='search_result', args=sgqlc.types.ArgDict((
        ('before', sgqlc.types.Arg(String, graphql_name='before', default=None)),
        ('after', sgqlc.types.Arg(String, graphql_name='after', default=None)),
        ('first', sgqlc.types.Arg(Int, graphql_name='first', default=None)),
        ('last', sgqlc.types.Arg(Int, graphql_name='last', default=None)),
))
    )


class SearchResultConnection(sgqlc.types.relay.Connection):
    __schema__ = schema
    __field_names__ = ('page_info', 'edges', 'total_count')
    page_info = sgqlc.types.Field(sgqlc.types.non_null(PageInfo), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('SearchResultEdge')), graphql_name='edges')
    total_count = sgqlc.types.Field(Int, graphql_name='total_count')


class SearchResultEdge(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field('SearchResult', graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class StrongMotionStationConnection(sgqlc.types.relay.Connection):
    __schema__ = schema
    __field_names__ = ('page_info', 'edges')
    page_info = sgqlc.types.Field(sgqlc.types.non_null(PageInfo), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('StrongMotionStationEdge')), graphql_name='edges')


class StrongMotionStationEdge(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field('StrongMotionStation', graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class TaskTaskRelation(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('parent', 'child', 'parent_id', 'child_id')
    parent = sgqlc.types.Field('GeneralTask', graphql_name='parent')
    child = sgqlc.types.Field('ChildTaskUnion', graphql_name='child')
    parent_id = sgqlc.types.Field(String, graphql_name='parent_id')
    child_id = sgqlc.types.Field(String, graphql_name='child_id')


class TaskTaskRelationConnection(sgqlc.types.relay.Connection):
    __schema__ = schema
    __field_names__ = ('page_info', 'edges', 'total_count')
    page_info = sgqlc.types.Field(sgqlc.types.non_null(PageInfo), graphql_name='pageInfo')
    edges = sgqlc.types.Field(sgqlc.types.non_null(sgqlc.types.list_of('TaskTaskRelationEdge')), graphql_name='edges')
    total_count = sgqlc.types.Field(Int, graphql_name='total_count')


class TaskTaskRelationEdge(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('node', 'cursor')
    node = sgqlc.types.Field(TaskTaskRelation, graphql_name='node')
    cursor = sgqlc.types.Field(sgqlc.types.non_null(String), graphql_name='cursor')


class UpdateAutomationTask(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('task_result',)
    task_result = sgqlc.types.Field('AutomationTask', graphql_name='task_result')


class UpdateGeneralTaskPayload(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('general_task', 'ok', 'client_mutation_id')
    general_task = sgqlc.types.Field('GeneralTask', graphql_name='general_task')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    client_mutation_id = sgqlc.types.Field(String, graphql_name='clientMutationId')


class UpdateOpenquakeHazardTask(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('ok', 'openquake_hazard_task')
    ok = sgqlc.types.Field(Boolean, graphql_name='ok')
    openquake_hazard_task = sgqlc.types.Field('OpenquakeHazardTask', graphql_name='openquake_hazard_task')


class UpdateRuptureGenerationTask(sgqlc.types.Type):
    __schema__ = schema
    __field_names__ = ('task_result',)
    task_result = sgqlc.types.Field('RuptureGenerationTask', graphql_name='task_result')


class AggregateInversionSolution(sgqlc.types.Type, Node, FileInterface, PredecessorsInterface, InversionSolutionInterface):
    __schema__ = schema
    __field_names__ = ('common_rupture_set', 'source_solutions', 'aggregation_fn')
    common_rupture_set = sgqlc.types.Field('File', graphql_name='common_rupture_set')
    source_solutions = sgqlc.types.Field(sgqlc.types.list_of('SourceSolutionUnion'), graphql_name='source_solutions')
    aggregation_fn = sgqlc.types.Field(AggregationFn, graphql_name='aggregation_fn')


class AutomationTask(sgqlc.types.Type, Node, Thing, AutomationTaskInterface):
    __schema__ = schema
    __field_names__ = ('model_type', 'task_type', 'inversion_solution')
    model_type = sgqlc.types.Field(ModelType, graphql_name='model_type')
    task_type = sgqlc.types.Field(TaskSubType, graphql_name='task_type')
    inversion_solution = sgqlc.types.Field('InversionSolutionUnion', graphql_name='inversion_solution')


class File(sgqlc.types.Type, Node, FileInterface, PredecessorsInterface):
    __schema__ = schema
    __field_names__ = ()


class GeneralTask(sgqlc.types.Type, Node, Thing):
    __schema__ = schema
    __field_names__ = ('updated', 'agent_name', 'title', 'description', 'argument_lists', 'swept_arguments', 'meta', 'notes', 'subtask_count', 'subtask_type', 'model_type', 'subtask_result')
    updated = sgqlc.types.Field(DateTime, graphql_name='updated')
    agent_name = sgqlc.types.Field(String, graphql_name='agent_name')
    title = sgqlc.types.Field(String, graphql_name='title')
    description = sgqlc.types.Field(String, graphql_name='description')
    argument_lists = sgqlc.types.Field(sgqlc.types.list_of(KeyValueListPair), graphql_name='argument_lists')
    swept_arguments = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='swept_arguments')
    meta = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePair), graphql_name='meta')
    notes = sgqlc.types.Field(String, graphql_name='notes')
    subtask_count = sgqlc.types.Field(Int, graphql_name='subtask_count')
    subtask_type = sgqlc.types.Field(TaskSubType, graphql_name='subtask_type')
    model_type = sgqlc.types.Field(ModelType, graphql_name='model_type')
    subtask_result = sgqlc.types.Field(EventResult, graphql_name='subtask_result')


class InversionSolution(sgqlc.types.Type, Node, InversionSolutionInterface, FileInterface, PredecessorsInterface):
    __schema__ = schema
    __field_names__ = ()


class InversionSolutionNrml(sgqlc.types.Type, Node, FileInterface, PredecessorsInterface):
    __schema__ = schema
    __field_names__ = ('created', 'source_solution')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    source_solution = sgqlc.types.Field('SourceSolutionUnion', graphql_name='source_solution')


class ObjectIdentity(sgqlc.types.Type, Node):
    __schema__ = schema
    __field_names__ = ('object_type', 'object_id', 'clazz_name', 'node_id')
    object_type = sgqlc.types.Field(String, graphql_name='object_type')
    object_id = sgqlc.types.Field(String, graphql_name='object_id')
    clazz_name = sgqlc.types.Field(String, graphql_name='clazz_name')
    node_id = sgqlc.types.Field(ID, graphql_name='node_id')


class OpenquakeHazardConfig(sgqlc.types.Type, Node, Thing):
    __schema__ = schema
    __field_names__ = ('source_models', 'template_archive')
    source_models = sgqlc.types.Field(sgqlc.types.list_of('OpenquakeNrmlUnion'), graphql_name='source_models')
    template_archive = sgqlc.types.Field(File, graphql_name='template_archive')


class OpenquakeHazardSolution(sgqlc.types.Type, Node, Thing, PredecessorsInterface):
    __schema__ = schema
    __field_names__ = ('config', 'csv_archive', 'hdf5_archive', 'modified_config', 'task_args', 'metrics', 'meta', 'produced_by')
    config = sgqlc.types.Field(OpenquakeHazardConfig, graphql_name='config')
    csv_archive = sgqlc.types.Field(File, graphql_name='csv_archive')
    hdf5_archive = sgqlc.types.Field(File, graphql_name='hdf5_archive')
    modified_config = sgqlc.types.Field(File, graphql_name='modified_config')
    task_args = sgqlc.types.Field(File, graphql_name='task_args')
    metrics = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePair), graphql_name='metrics')
    meta = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePair), graphql_name='meta')
    produced_by = sgqlc.types.Field('OpenquakeHazardTask', graphql_name='produced_by')


class OpenquakeHazardTask(sgqlc.types.Type, Node, Thing, AutomationTaskInterface):
    __schema__ = schema
    __field_names__ = ('config', 'hazard_solution', 'model_type', 'task_type')
    config = sgqlc.types.Field(OpenquakeHazardConfig, graphql_name='config')
    hazard_solution = sgqlc.types.Field(OpenquakeHazardSolution, graphql_name='hazard_solution')
    model_type = sgqlc.types.Field(ModelType, graphql_name='model_type')
    task_type = sgqlc.types.Field(OpenquakeTaskType, graphql_name='task_type')


class RuptureGenerationTask(sgqlc.types.Type, Node, Thing, AutomationTaskInterface):
    __schema__ = schema
    __field_names__ = ()


class ScaledInversionSolution(sgqlc.types.Type, Node, FileInterface, PredecessorsInterface, InversionSolutionInterface):
    __schema__ = schema
    __field_names__ = ('source_solution',)
    source_solution = sgqlc.types.Field('SourceSolutionUnion', graphql_name='source_solution')


class SmsFile(sgqlc.types.Type, Node, FileInterface):
    __schema__ = schema
    __field_names__ = ('file_type',)
    file_type = sgqlc.types.Field(sgqlc.types.non_null(SmsFileType), graphql_name='file_type')


class StrongMotionStation(sgqlc.types.Type, Node, Thing):
    __schema__ = schema
    __field_names__ = ('updated', 'site_code', 'site_class', 'site_class_basis', 'vs30_mean', 'vs30_std_dev', 'bedrock_encountered', 'liquefiable', 'soft_clay_or_peat')
    updated = sgqlc.types.Field(DateTime, graphql_name='updated')
    site_code = sgqlc.types.Field(String, graphql_name='site_code')
    site_class = sgqlc.types.Field(SmsSiteClass, graphql_name='site_class')
    site_class_basis = sgqlc.types.Field(SmsSiteClassBasis, graphql_name='site_class_basis')
    vs30_mean = sgqlc.types.Field(sgqlc.types.list_of(Float), graphql_name='Vs30_mean')
    vs30_std_dev = sgqlc.types.Field(sgqlc.types.list_of(Float), graphql_name='Vs30_std_dev')
    bedrock_encountered = sgqlc.types.Field(Boolean, graphql_name='bedrock_encountered')
    liquefiable = sgqlc.types.Field(Boolean, graphql_name='liquefiable')
    soft_clay_or_peat = sgqlc.types.Field(Boolean, graphql_name='soft_clay_or_peat')


class Table(sgqlc.types.Type, Node):
    __schema__ = schema
    __field_names__ = ('name', 'object_id', 'created', 'column_headers', 'column_types', 'rows', 'meta', 'table_type', 'dimensions')
    name = sgqlc.types.Field(String, graphql_name='name')
    object_id = sgqlc.types.Field(ID, graphql_name='object_id')
    created = sgqlc.types.Field(DateTime, graphql_name='created')
    column_headers = sgqlc.types.Field(sgqlc.types.list_of(String), graphql_name='column_headers')
    column_types = sgqlc.types.Field(sgqlc.types.list_of(RowItemType), graphql_name='column_types')
    rows = sgqlc.types.Field(sgqlc.types.list_of(sgqlc.types.list_of(String)), graphql_name='rows')
    meta = sgqlc.types.Field(sgqlc.types.list_of(KeyValuePair), graphql_name='meta')
    table_type = sgqlc.types.Field(TableType, graphql_name='table_type')
    dimensions = sgqlc.types.Field(sgqlc.types.list_of(KeyValueListPair), graphql_name='dimensions')


class TimeDependentInversionSolution(sgqlc.types.Type, Node, FileInterface, PredecessorsInterface, InversionSolutionInterface):
    __schema__ = schema
    __field_names__ = ('source_solution',)
    source_solution = sgqlc.types.Field(InversionSolution, graphql_name='source_solution')



########################################################################
# Unions
########################################################################
class AutomationTaskUnion(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (RuptureGenerationTask, AutomationTask)


class ChildTaskUnion(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (GeneralTask, RuptureGenerationTask, AutomationTask, OpenquakeHazardTask)


class FileUnion(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (SmsFile, File, InversionSolution, ScaledInversionSolution, AggregateInversionSolution, InversionSolutionNrml, TimeDependentInversionSolution)


class InversionSolutionUnion(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (InversionSolution, ScaledInversionSolution, AggregateInversionSolution, TimeDependentInversionSolution)


class OpenquakeNrmlUnion(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (File, InversionSolutionNrml)


class PredecessorUnion(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (File, AggregateInversionSolution, InversionSolution, ScaledInversionSolution, InversionSolutionNrml, TimeDependentInversionSolution)


class SearchResult(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (AggregateInversionSolution, AutomationTask, File, GeneralTask, InversionSolution, InversionSolutionNrml, OpenquakeHazardConfig, OpenquakeHazardSolution, OpenquakeHazardTask, RuptureGenerationTask, ScaledInversionSolution, SmsFile, StrongMotionStation, TimeDependentInversionSolution)


class SourceSolutionUnion(sgqlc.types.Union):
    __schema__ = schema
    __types__ = (AggregateInversionSolution, InversionSolution, ScaledInversionSolution, TimeDependentInversionSolution)



########################################################################
# Schema Entry Points
########################################################################
schema.query_type = QueryRoot
schema.mutation_type = MutationRoot
schema.subscription_type = None

