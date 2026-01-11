package main

import (
	"context"
	"testing"

	"github.com/google/go-cmp/cmp"
	"google.golang.org/protobuf/testing/protocmp"
	"google.golang.org/protobuf/types/known/durationpb"
	"google.golang.org/protobuf/types/known/structpb"

	fnv1 "github.com/crossplane/function-sdk-go/proto/v1"
	"github.com/crossplane/function-sdk-go/response"
)

func TestRunFunction(t *testing.T) {
	type args struct {
		ctx context.Context
		req *fnv1.RunFunctionRequest
	}
	type want struct {
		rsp *fnv1.RunFunctionResponse
		err error
	}

	cases := map[string]struct {
		reason string
		args   args
		want   want
	}{
		"AddLabelToResource": {
			reason: "Should add label to desired resources",
			args: args{
				req: &fnv1.RunFunctionRequest{
					Desired: &fnv1.State{
						Resources: map[string]*fnv1.Resource{
							"test-resource": {
								Resource: mustStructJSON(`{"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "foo"}}`),
							},
						},
					},
				},
			},
			want: want{
				rsp: &fnv1.RunFunctionResponse{
					Meta: &fnv1.ResponseMeta{Ttl: durationpb.New(response.DefaultTTL)},
					Desired: &fnv1.State{
						Resources: map[string]*fnv1.Resource{
							"test-resource": {
								Resource: mustStructJSON(`{"apiVersion": "v1", "kind": "ConfigMap", "metadata": {"name": "foo", "labels": {"vellum.io/managed-by": "crossplane-go"}}}`),
							},
						},
					},
				},
			},
		},
	}

	for name, tc := range cases {
		t.Run(name, func(t *testing.T) {
			f := &Function{}
			got, err := f.RunFunction(tc.args.ctx, tc.args.req)

			if diff := cmp.Diff(tc.want.err, err, protocmp.Transform()); diff != "" {
				t.Errorf("\n%s\nRunFunction(...) error diff:\n%s", tc.reason, diff)
			}

			if diff := cmp.Diff(tc.want.rsp, got, protocmp.Transform()); diff != "" {
				t.Errorf("\n%s\nRunFunction(...) response diff:\n%s", tc.reason, diff)
			}
		})
	}
}

func mustStructJSON(j string) *structpb.Struct {
	s := &structpb.Struct{}
	if err := s.UnmarshalJSON([]byte(j)); err != nil {
		panic(err)
	}
	return s
}
